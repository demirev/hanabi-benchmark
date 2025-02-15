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
  - OpenAI 
  - Anthropic 
  - Google
  - Groq
  - xAI
- Chain-of-thought reasoning configuration
- Detailed game state tracking and logging
- Experiment runner with CSV output
- Summary statistics generation

## Usage

```bash
git clone https://github.com/demirev/hanabi-benchmark.git
cd hanabi-benchmark
pip install -r requirements.txt

# Run with default settings (10 runs for all models)
python main.py

# Run with custom settings
python main.py \
    --num-runs 5 \
    --output-dir results \
    --models "openai/gpt-4o-mini-2024-07-18/{'cot':0}" \
    --debug
```

### Command Line Arguments

- `--num-runs`, `-n`: Number of games to run per model configuration (default: 10)
- `--output-dir`, `-o`: Directory where results will be saved (default: 'results')
- `--models`, `-m`: Comma-separated list of models to test in the format `provider/model/{"args"}`. If not specified, all models from the configuration will be tested
  - Example: `"openai/gpt-4/{'cot':1},anthropic/claude-3-opus-20240229/{'cot':0}"`
  - Supported providers: openai, anthropic, google, groq, xai, test
  - The args JSON object can include configuration like chain-of-thought prompting (`cot`)
- `--debug`, `-d`: Enable debug mode to see detailed prompts and responses from the first player

Make sure to set the correct API keys in the `.env`