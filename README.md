# Hanabi Benchmark

A framework for testing Large Language Models' reasoning capabilities through the cooperative card game Hanabi.

## LEADERBOARD

Coming soon...

## Overview

This project implements a simulated version of Hanabi, a cooperative card game, where multiple LLM agents work together to achieve the highest possible score. The framework supports various LLM providers (OpenAI GPT, Anthropic Claude, Google Gemini) and allows testing different reasoning approaches through chain-of-thought prompting.

## Game Rules

Hanabi is a cooperative card game where players work together to build five firework displays (one for each color) by playing cards in ascending order (1-5). Players can see everyone's cards except their own, requiring careful communication and deduction. On thier turn, players can a) play a card on the board, b) discard a card, or c) give a hint to another player.

- 5 colors: Red, Green, Blue, Yellow, White
- Numbers: 1-5 for each color
- 3 lives (mistakes allowed)
- 8 information tokens for giving hints
- 4 cards per player
- 5 players per game

## Prompt Details

At each turn of the game, agents receive a text representation of the current game state and a list of the actions taken by other players since their last turn.

An example game state is shown below:

```
Players: Player 1, Player 2, [YOU], Player 4, Player 5
Lives: 2/3 | Information tokens: 4/8 | Score: 7/25
Discard pile:
R1 R1 G1 G2 B1 Y1 W2
Play area:
[R2] [G1] [B2] [Y1] [W1]
Your hand:
[*] [*] [*] [*]
Other hands:
Player 1: [R4] [G3] [B1] [Y2] [W3]
Player 2: [R1] [G4] [B3] [Y3] [W4]
Player 4: [R2] [G2] [B2] [Y4] [W2]
Player 5: [R3] [G3] [B3] [Y2] [W3]
```

Agents must respond with a move in one of the following formats:

> `P4`

This move will play the card 4 from your hand.

> `D1`

This move will discard the card 1 from your hand.

> `C2N3124`

This move will give a hint to player 2 that their cards 1,2,4 are 3s.

An incorrectly formatted move will result in a loss of 1 life and will not be added to the game state and history.

## Features

- Support for multiple LLM providers:
  - OpenAI (gpt-4o, gpt-03)
  - Anthropic (claude-3-5-sonnet-20240620)
  - Google (gemini-1.5-flash-latest)
  - Groq (mixtral-8x7b-32768)
  - xAI
  - Random baseline player
- Chain-of-thought reasoning configuration
- Detailed game state tracking and logging
- Experiment runner with CSV output
- Summary statistics generation

## Usage

```bash
git clone https://github.com/demirev/hanabi-benchmark.git
cd hanabi-benchmark
pip install -r requirements.txt
python main.py --num_runs 10
```

Make sure to set the correct API keys in the `.env` file for each provider.

## Acknowledgements

Hanabi is a game created by Antoine Bauza.
