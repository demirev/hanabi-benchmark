# Hanabi Benchmark

A framework for testing Large Language Models' reasoning capabilities through the cooperative card game Hanabi.

## LEADERBOARD
| Model | Provider | Chain of Thought | Avg Score (out of 25) | Win % | Avg Turns |
|-------|----------|------------------|----------------------|--------|------------|
| gpt-5-2025-08-07 (high) | OpenAI | No | 13.0 | 0 | 53.0 |
| grok-4-0709 | xAI | No | 10.0 | 0 | 39.0 |
| o3-mini-2025-01-31 (high) | OpenAI | No | 6.8 | 0 | 59.8 |
| o4-mini-2025-04-16 | OpenAI | No | 4.3 | 0 | 37.0 |
| o3-mini-2025-01-31 (medium) | OpenAI | No | 3.1 | 0 | 48.2 |
| claude-3-7-sonnet-20250219 (16000 reasoning) | Anthropic | No | 2.9 | 0 | 14.4 |
| grok-3-mini-beta | xAI | No | 2.4 | 0 | 14.4 |
| gemini-2.5-pro-exp-03-25 | Google | No | 2.4 | 0 | 10.8 |
| claude-3-7-sonnet-20250219 (4096 reasoning) | Anthropic | No | 1.5 | 0 | 11.7 |
| o3-mini-2025-01-31 (low) | OpenAI | No | 1.3 | 0 | 11.5 |
| claude-3-5-sonnet-20241022 | Anthropic | Yes | 1.3 | 0 | 10.5 |
| grok-2-1212 | xAI | No | 1.1 | 0 | 4.1 |
| deepseek-r1-distill-llama-70b | Groq | No | 1.0 | 0 | 4.3 |
| gpt-4.1-2025-04-14 | OpenAI | Yes | 0.7 | 0 | 5.9 |
| grok-2-1212 | xAI | Yes | 0.6 | 0 | 5.1 |
| claude-3-haiku-20240307 | Anthropic | No | 0.6 | 0 | 3.6 |
| llama3-70b-8192 | Groq | No | 0.6 | 0 | 3.6 |
| deepseek-r1-distill-qwen-32b | Groq | No | 0.5 | 0 | 9.0 |
| claude-3-7-sonnet-20250219 | Anthropic | No | 0.4 | 0 | 5.0 |
| gemma2-9b-it | Groq | No | 0.4 | 0 | 3.4 |
| claude-3-sonnet-20240229 | Anthropic | No | 0.3 | 0 | 3.4 |
| gpt-4o-2024-08-06 | OpenAI | Yes | 0.2 | 0 | 4.3 |
| claude-3-5-sonnet-20241022 | Anthropic | No | 0.1 | 0 | 4.3 |
| gpt-4.5-preview-2025-02-27 | OpenAI | No | 0.1 | 0 | 3.6 |

*Note: Only showing models with non-zero scores.*

Last updated: 2025-08-07

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
- `--models`, `-m`: Semicolon-separated list of models to test in the format `provider/model/{"args"}`. If not specified, all models from the configuration will be tested
  - Example: `"openai/gpt-4/{'cot':1};anthropic/claude-3-opus-20240229/{'cot':0}"`
  - Supported providers: openai, anthropic, google, groq, xai, test
  - The args JSON object can include configuration like chain-of-thought prompting (`cot`)
- `--provider`, `-p`: Filter models by provider name (e.g., "openai", "anthropic", etc.)
- `--only-new`: Only run models that haven't been tested in previous experiments
- `--debug`, `-d`: Enable debug mode to see detailed prompts and responses from the first player

Make sure to set the correct API keys in the `.env`