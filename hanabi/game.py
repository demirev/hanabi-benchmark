from dataclasses import dataclass
from typing import List, Dict, Optional
import random
from hanabi.players import Player

@dataclass
class Card:
    color: str  # R,G,B,Y,W
    number: int # 1-5

class HanabiGame:
    def __init__(self, players: List['Player']):
        self.players = players
        self.current_player = 0
        self.lives = 3
        self.info_tokens = 8
        self.turns_played = 0
        self.play_area = {'R': 0, 'G': 0, 'B': 0, 'Y': 0, 'W': 0}
        self.discard_pile: List[Card] = []
        self.hands: List[List[Card]] = []
        self.deck = self._create_deck()
        self._deal_initial_hands()
    
    def _create_deck(self) -> List[Card]:
        deck = []
        for color in 'RGBYW':
            for number, count in [(1,3), (2,2), (3,2), (4,2), (5,1)]:
                for _ in range(count):
                    deck.append(Card(color, number))
        random.shuffle(deck)
        return deck
    
    def _deal_initial_hands(self):
        self.hands = [[] for _ in range(len(self.players))]
        for player in range(len(self.players)):
            for _ in range(4):
                self.hands[player].append(self.deck.pop())

    def get_game_state(self, player: int, current_player: int) -> str:
        state = f"Players: {', '.join(f'Player {i+1}' for i in range(len(self.players))).replace(f'Player {player+1}', '[YOU]')}\n"
        state += f"Lives: {self.lives}/3 | Information tokens: {self.info_tokens}/8 | Score: {sum(self.play_area.values())}/25\n\n"

        if player == current_player:
            state += f"Player {current_player+1} (YOU) to play\n"
        else:
            state += f"Player {current_player+1} to play\n"

        state += "Discard pile:\n"
        state += " ".join(f"{c.color}{c.number}" for c in self.discard_pile) + "\n\n"
        
        state += "Play area:\n"
        state += " ".join(f"[{color}{value}]" for color, value in self.play_area.items() if value > 0) + "\n\n"
        
        state += "Your hand:\n"
        state += " ".join("[*]" * len(self.hands[player])) + "\n\n"
        
        state += "Other hands:\n"
        for i in range(len(self.players)):
            if i != player:
                state += f"Player {i+1}: {' '.join(f'[{c.color}{c.number}]' for c in self.hands[i])}\n"

        #state += "----------------------------------------\n\n"
        return state.strip()  # Ensure no trailing newlines
    
    def validate_move(self, player: int, move: str) -> bool:
        try:
            if move.startswith('P'):  # Play
                if len(move) != 2: # P <card_idx>
                    return False
                card_idx = int(move[1]) - 1
                return card_idx < len(self.hands[player])
                
            elif move.startswith('D'):  # Discard
                if len(move) != 2: # D <card_idx>
                    return False
                card_idx = int(move[1]) - 1
                return card_idx < len(self.hands[player]) and self.info_tokens < 8
                
            elif move.startswith('C'):  # Clue
                if self.info_tokens <= 0:
                    return False
                if len(move) < 5: # C <target> <type> <value> <positions>
                    return False
                target = int(move[1]) - 1
                clue_type = move[2]
                value = move[3]
                positions = set(int(x)-1 for x in move[4:])
                
                if clue_type == 'N':
                    value = int(value)
                    matching = {i for i, card in enumerate(self.hands[target]) 
                              if card.number == value}
                else:  # Color clue
                    matching = {i for i, card in enumerate(self.hands[target]) 
                              if card.color == value}
                return positions == matching
                
            return False
        except:
            return False

    def execute_move(self, player: int, move: str):
        self.turns_played += 1

        if not self.validate_move(player, move):
            self.lives -= 1
            return "INVALID MOVE"
            
        if move.startswith('P'):
            card_idx = int(move[1]) - 1
            card = self.hands[player].pop(card_idx)
            if self.play_area[card.color] == card.number - 1:
                self.play_area[card.color] = card.number
            else:
                self.lives -= 1
                self.discard_pile.append(card)
            if self.deck:
                self.hands[player].insert(card_idx, self.deck.pop())
                
        elif move.startswith('D'):
            card_idx = int(move[1]) - 1
            card = self.hands[player].pop(card_idx)
            self.discard_pile.append(card)
            if self.deck:
                self.hands[player].insert(card_idx, self.deck.pop())
            self.info_tokens = min(8, self.info_tokens + 1)
            
        elif move.startswith('C'):
            self.info_tokens -= 1

        return move

    def play_game(self, verbosity: int = 1):
        if verbosity > 0:
            print("Starting game...")

        history = ["" for _ in range(len(self.players))] # initialize empty history for each player

        while self.lives > 0 and sum(self.play_area.values()) < 25 and self.deck:
            if verbosity > 1:
                print(f">>> Player {self.current_player+1}, Turn {self.turns_played}")
                print(f">>> Game State: \n{self.get_game_state(self.current_player, self.current_player)}") # full game state
            elif verbosity > 0:
                print(f">>> Player {self.current_player+1}, Turn {self.turns_played}")
                top_line = self.get_game_state(self.current_player, self.current_player).split('\n')[1]
                print(f">>> Game State: {top_line}") # top line of game state
            
            # current state from the view point of each player
            current_states = [
                self.get_game_state(player, self.current_player) 
                for player in range(len(self.players))
            ]
            
            # create current state string, including turns since last move
            if history[self.current_player] != "":
                new_state = history[self.current_player]
                new_state += f"\n<-------- Current State: Turn {self.turns_played}, Player {self.current_player+1} (You) -------->\n"
                new_state += f"{current_states[self.current_player]}\n"
            else:
                new_state = current_states[self.current_player]
            
            # decide move
            move = self.players[self.current_player].take_turn(new_state)

            # execute move
            if verbosity > 0:
                print(f">>> Player {self.current_player+1} move: {move}")
                
            executed_move = self.execute_move(self.current_player, move)

            # update history
            for player in range(len(self.players)):
                history[player] += f"\n<-------- Turn {self.turns_played-1}, Player {self.current_player+1} -------->\n"  # -1 because we are adding the move after the turn
                history[player] += f"<-- Game State -->\n{current_states[player]}\n"
                history[player] += f"<-- Move -->\n{executed_move}\n\n"

            history[self.current_player] = "" # reset history for current player, it will start accumulating again from next player's turn

            # switch to next player
            self.current_player = (self.current_player + 1) % len(self.players)

        if verbosity > 0:
            print("Game over. Final board state:")
            print(self.get_game_state(self.current_player, self.current_player))
        
        return sum(self.play_area.values()) 