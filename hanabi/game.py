from dataclasses import dataclass
from typing import List, Dict, Optional
import random
from hanabi.player import Player

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
        self.play_area = {'R': 0, 'G': 0, 'B': 0, 'Y': 0, 'W': 0}
        self.discard_pile: List[Card] = []
        self.hands: List[List[Card]] = []
        self.last_actions: List[str] = []
        self.deck = self._create_deck()
        self._deal_initial_hands()
        self.last_states: List[tuple[int, str, str]] = []  # (player, action, state)
    
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

    def get_game_state(self, player: int) -> str:
        state = f"Players: {', '.join(f'Player {i+1}' for i in range(len(self.players))).replace(f'Player {player+1}', '[YOU]')}\n"
        state += f"Lives: {self.lives}/3 | Information tokens: {self.info_tokens}/8 | Score: {sum(self.play_area.values())}/25\n\n"
        
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
        return state
    
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
        if not self.validate_move(player, move):
            self.lives -= 1
            self.last_actions.append("INVALID MOVE")
            # Store the state after invalid move
            self.last_states.append((player, "INVALID MOVE", self.get_game_state(player)))
            return
            
        if move.startswith('P'):
            card_idx = int(move[1]) - 1
            card = self.hands[player].pop(card_idx)
            if self.play_area[card.color] == card.number - 1:
                self.play_area[card.color] = card.number
            else:
                self.lives -= 1
                self.discard_pile.append(card)
            if self.deck:
                self.hands[player].append(self.deck.pop())
                
        elif move.startswith('D'):
            card_idx = int(move[1]) - 1
            card = self.hands[player].pop(card_idx)
            self.discard_pile.append(card)
            if self.deck:
                self.hands[player].append(self.deck.pop())
            self.info_tokens = min(8, self.info_tokens + 1)
            
        elif move.startswith('C'):
            self.info_tokens -= 1
            
        self.last_actions.append(move)
        # Store the state after the move
        self.last_states.append((player, move, self.get_game_state(player)))

    def play_game(self):
        while self.lives > 0 and sum(self.play_area.values()) < 25 and self.deck:
            player = self.current_player
            current_state = self.get_game_state(player)
            
            # Get relevant states since player's last turn
            relevant_states = self.last_states[-(len(self.players)-1):]
            
            # Format the history with intermediate states
            history = []
            for p, action, state in relevant_states:
                history.append(f"Player {p+1} Turn:")
                history.append(f"Action: {action}")
                history.append("Board State:")
                history.append(state)
                history.append("-" * 45)
            
            new_state = current_state
            if history:
                new_state += "\nPrevious turns:\n" + "\n".join(history)
            
            move = self.players[player].take_turn(new_state)
            self.execute_move(player, move)
            self.current_player = (self.current_player + 1) % len(self.players)
        
        return sum(self.play_area.values()) 