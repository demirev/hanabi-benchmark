from abc import ABC, abstractmethod
import random
from typing import List, Optional
from openai import OpenAI
import os
from anthropic import Anthropic
import google.generativeai as genai
from groq import Groq


class Player(ABC):
	def __init__(self):
		self.history = []  # List of (game_state, action) tuples
	
	@abstractmethod
	def _generate_move(self, game_state: str) -> str:
		"""Generate the next move based on the current game state."""
		pass
	
	def take_turn(self, game_state: str) -> str:
		"""
		Process the game state and return a move.
		Stores the interaction in history.
		"""
		move = self._generate_move(game_state)
		self.history.append((game_state, move))
		return move


class PromptLoaderMixin:
	def _load_prompts(self, system_prompt: Optional[str] = None, 
					 play_suffix: Optional[str] = None, 
					 think_suffix: Optional[str] = None):
		# Load default system prompt if none provided
		if system_prompt is None:
			with open("prompts/system.txt", "r") as f:
				system_prompt = f.read()
		
		# Load default play suffix if none provided
		if play_suffix is None:
			with open("prompts/play_suffix.txt", "r") as f:
				play_suffix = f.read()

		# Load default think suffix if none provided
		if think_suffix is None:
			with open("prompts/think_suffix.txt", "r") as f:
				think_suffix = f.read()

		self.system_prompt = system_prompt
		self.play_suffix = play_suffix
		self.think_suffix = think_suffix


class RandomPlayer(Player):
	def _generate_move(self, game_state: str) -> str:
		
		# If game state includes a line "Previous turns:", remove everything after it
		if "Previous turns:" in game_state:
			game_state = game_state.split("Previous turns:")[0]

		# Parse the game state to get number of cards in hand
		hand_line = [line for line in game_state.split('\n') if "Your hand:" in line][0]
		num_cards = len([c for c in hand_line if c == '*'])
		
		# Parse info tokens
		info_line = [line for line in game_state.split('\n') if "Information tokens:" in line][0]
		info_tokens = int(info_line.split(':')[1].split('/')[0].strip())
		
		# Generate possible moves
		possible_moves = []
		
		# Add play moves
		for i in range(num_cards):
			possible_moves.append(f"P{i+1}")
		
		# Add discard moves (only if not at max info tokens)
		if info_tokens < 8:
			for i in range(num_cards):
				possible_moves.append(f"D{i+1}")
		
		# Add clue moves (only if have info tokens)
		if info_tokens > 0:
			# Get other players' hands
			other_hands_section = game_state.split("Other hands:\n")[1].split("\n")
			for line in other_hands_section:
				if ':' in line:  # Only process lines that contain player hands
					# print(line)
					player_num = line.split(':')[0].split()[1]
					cards = line.split(':')[1].strip()
					if cards:  # If player has cards
						# Add color clues
						for color in 'RGBYW':
							positions = []
							for i, card in enumerate(cards.split()):
								if card[1] == color:  # [R1] format
									positions.append(str(i+1))
							if positions:  # Only add if there are matching cards
								possible_moves.append(f"C{player_num}C{color}{''.join(positions)}")
						
						# Add number clues
						for number in range(1, 6):
							positions = []
							for i, card in enumerate(cards.split()):
								if int(card[2]) == number:  # [R1] format
									positions.append(str(i+1))
							if positions:  # Only add if there are matching cards
								possible_moves.append(f"C{player_num}N{number}{''.join(positions)}")
		
		return random.choice(possible_moves)


class GPTPlayer(Player, PromptLoaderMixin):
	def __init__(
			self, 
			model: str = "gpt-3.5-turbo", 
			api_key: Optional[str] = None, 
			cot: int = 0, 
			system_prompt: Optional[str] = None, 
			play_suffix: Optional[str] = None, 
			think_suffix: Optional[str] = None,
			base_url: Optional[str] = None # to use Groq or Xai, set to their base_url instead of None
		): 
		super().__init__()
		self.client = OpenAI(
			api_key=api_key,
			base_url=base_url  # Will use OpenAI's default if None, or can be set to Groq's URL
		)
		self.model = model
		self.cot = cot
		
		self._load_prompts(system_prompt, play_suffix, think_suffix)

		# Initialize conversation with system prompt
		self.messages = [
			{"role": "system", "content": self.system_prompt}
		]
	
	def _generate_move(self, game_state: str) -> str:
		# Add game state to conversation history
		self.messages.append({"role": "user", "content": game_state})
		
		try:
			for i in range(self.cot + 1): 
				
				if i == self.cot:
					self.messages.append({
						"role": "user", 
						"content": self.play_suffix
					})
				else:
					self.messages.append({
						"role": "user", 
						"content": self.think_suffix
					})
				
				# Get response from API
				response = self.client.chat.completions.create(
					model=self.model,
					messages=self.messages
				)

				# Extract move from response
				output = response.choices[0].message.content.strip()
          
				# Add response to conversation history
				self.messages.append({
					"role": "assistant",
					"content": output
				})
				
			
			return output # the final output is the move
			
		except Exception as e:
			print(f"Error generating move: {e}")
			return "ERROR" # this will be interpreted by the game as an invalid move and the player will lose 1 life


class ClaudePlayer(Player, PromptLoaderMixin):
	def __init__(self, model: str = "claude-3-sonnet-20240229", api_key: Optional[str] = None, 
				 cot: int = 0, system_prompt: Optional[str] = None, 
				 play_suffix: Optional[str] = None, think_suffix: Optional[str] = None):
		super().__init__()
		self.client = Anthropic(api_key=api_key)
		self.model = model
		self.cot = cot
		
		self._load_prompts(system_prompt, play_suffix, think_suffix)
	
	def _generate_move(self, game_state: str) -> str:
		# Add game state to conversation history
		self.messages.append({"role": "user", "content": game_state})
		
		try:
			for i in range(self.cot + 1):
				if i == self.cot:
					self.messages.append({
						"role": "user", 
						"content": self.play_suffix
					})
				else:
					self.messages.append({
						"role": "user", 
						"content": self.think_suffix
					})
				
				# Get response from API
				response = self.client.messages.create(
					model=self.model,
					messages=self.messages,
					system=self.system_prompt # anthropic requires system prompt per message
				)

				# Extract move from response
				output = response.content[0].text
				
				# Add response to conversation history
				self.messages.append({
					"role": "assistant",
					"content": output
				})
			
			return output # the final output is the move
			
		except Exception as e:
			print(f"Error generating move: {e}")
			return "ERROR"


class GeminiPlayer(Player, PromptLoaderMixin):
	def __init__(self, model: str = "gemini-pro", api_key: Optional[str] = None, 
				 cot: int = 0, system_prompt: Optional[str] = None, 
				 play_suffix: Optional[str] = None, think_suffix: Optional[str] = None):
		super().__init__()
		if api_key:
			genai.configure(api_key=api_key)
		self.cot = cot
		
		self._load_prompts(system_prompt, play_suffix, think_suffix)
		
		self.model = genai.GenerativeModel(model, system_instruction=self.system_prompt)
		self.chat = self.model.start_chat(history=[])
		
	def _generate_move(self, game_state: str) -> str:
		try:
			# Send game state
			self.chat.send_message(game_state)
			
			for i in range(self.cot + 1):
				if i == self.cot:
					response = self.chat.send_message(self.play_suffix)
				else:
					response = self.chat.send_message(self.think_suffix)
				
				output = response.text
			
			return output # the final output is the move
			
		except Exception as e:
			print(f"Error generating move: {e}")
			return "ERROR"


class GroqPlayer(Player, PromptLoaderMixin):
	def __init__(self, model: str = "mixtral-8x7b-32768", api_key: Optional[str] = None, 
				 cot: int = 0, system_prompt: Optional[str] = None, 
				 play_suffix: Optional[str] = None, think_suffix: Optional[str] = None):
		super().__init__()
		self.client = Groq(api_key=api_key)
		self.model = model
		self.cot = cot
		
		self._load_prompts(system_prompt, play_suffix, think_suffix)

		# Initialize conversation with system prompt
		self.messages = [
			{"role": "system", "content": self.system_prompt}
		]
	
	def _generate_move(self, game_state: str) -> str:
		# Add game state to conversation history
		self.messages.append({"role": "user", "content": game_state})
		
		try:
			for i in range(self.cot + 1):
				if i == self.cot:
					self.messages.append({
						"role": "user", 
						"content": self.play_suffix
					})
				else:
					self.messages.append({
						"role": "user", 
						"content": self.think_suffix
					})
				
				# Get response from API
				response = self.client.chat.completions.create(
					model=self.model,
					messages=self.messages,
					temperature=0.2
				)

				# Extract move from response
				output = response.choices[0].message.content
				
				# Add response to conversation history
				self.messages.append({
					"role": "assistant",
					"content": output
				})
			
			return output # the final output is the move
			
		except Exception as e:
			print(f"Error generating move: {e}")
			return "ERROR"

