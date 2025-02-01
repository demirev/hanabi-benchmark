import argparse
from datetime import datetime
import csv
import os
from typing import List, Dict
import pandas as pd
from dotenv import load_dotenv
from hanabi.game import HanabiGame
from hanabi.players import (
	GPTPlayer,
	ClaudePlayer,
	GeminiPlayer,
	#GroqPlayer,
	RandomPlayer
)

# Load environment variables from .env file
load_dotenv()


AVAILABLE_MODELS = [
	{"provider": "openai", "model": "gpt-4", "args": {"cot": 1}},
	{"provider": "openai", "model": "gpt-3.5-turbo", "args": {"cot": 1}},
	{"provider": "anthropic", "model": "claude-3-sonnet-20240229", "args": {"cot": 1}},
	{"provider": "google", "model": "gemini-pro", "args": {"cot": 1}},
	{"provider": "groq", "model": "mixtral-8x7b-32768", "args": {"cot": 1}},
	{"provider": "test", "model": "random", "args": {"cot": 0}}
]


def get_player_class(provider: str) -> type:
	player_classes = {
		"openai": GPTPlayer,
		"anthropic": ClaudePlayer,
		"google": GeminiPlayer,
		"groq": GPTPlayer, # compatible API with OpenAI
		"xai": GPTPlayer, # compatible API with OpenAI
		"test": RandomPlayer
	}
	return player_classes[provider]


def create_player(provider: str, model: str, args: Dict) -> object:
	PlayerClass = get_player_class(provider)
	
	# Get API key from environment variables
	api_key = os.getenv(f"{provider.upper()}_API_KEY")
	
	if provider == "test":
		return PlayerClass()
	
	return PlayerClass(
		model=model,
		api_key=api_key,
		**args  # Pass all run arguments to the player
	)


def run_experiments(num_runs: int, output_dir: str = "results"):
	# Create output directory if it doesn't exist
	os.makedirs(output_dir, exist_ok=True)
	
	results_file = os.path.join(output_dir, "experiment_results.csv")
	summary_file = os.path.join(output_dir, "model_summary.csv")
	
	# Create results file with headers if it doesn't exist
	if not os.path.exists(results_file):
		with open(results_file, 'w', newline='') as f:
			writer = csv.writer(f)
			writer.writerow([
				"experiment_id",
				"provider",
				"model",
				"args",
				"timestamp",
				"score"
			])
	
	experiment_id = 1
	if os.path.exists(results_file):
		df = pd.read_csv(results_file)
		if not df.empty:
			experiment_id = df['experiment_id'].max() + 1
	
	# Run experiments for each model
	for model_config in AVAILABLE_MODELS:
		provider = model_config["provider"]
		model_name = model_config["model"]
		args = model_config["args"]
		num_players = 5
		
		print(f"\n\nRunning {num_runs} games for {provider} - {model_name} with args {args}")
		
		for run in range(num_runs):
			print(f"Run {run + 1}/{num_runs} {provider} - {model_name} with args {args} -------------------------------")
			
			# Create player and game
			players = [create_player(provider, model_name, args) for _ in range(num_players)]
			game = HanabiGame(players)
			
			# Run game and get score
			score = game.play_game(verbosity=2)
			
			# Save results
			with open(results_file, 'a', newline='') as f:
				writer = csv.writer(f)
				writer.writerow([
					experiment_id,
					provider,
					model_name,
					str(args),  # Convert dict to string for CSV storage
					datetime.now().isoformat(),
					score
				])
			
			experiment_id += 1
	
	# Generate summary after all experiments
	generate_summary(results_file, summary_file)


def generate_summary(results_file: str, summary_file: str):
	df = pd.read_csv(results_file)
	
	# Convert timestamp to datetime
	df['timestamp'] = pd.to_datetime(df['timestamp'])
	
	# Get the latest experiment for each model configuration
	latest_experiment = df.sort_values('timestamp').groupby(['provider', 'model', 'args']).last()
	
	# Calculate summary statistics
	summary = df.groupby(['provider', 'model', 'args']).agg({
		'score': ['mean', 'std', 'count']
	}).round(2)
	
	# Calculate win percentage (score of 25 is a win)
	win_pct = df[df['score'] == 25].groupby(['provider', 'model', 'args']).size() / \
			  df.groupby(['provider', 'model', 'args']).size() * 100
	
	summary['win_percentage'] = win_pct.round(2)
	
	# Flatten column names
	summary.columns = ['avg_score', 'std_score', 'num_games', 'win_percentage']
	
	# Save summary
	summary.to_csv(summary_file)
	print(f"\nSummary saved to {summary_file}")


def main():
	parser = argparse.ArgumentParser(description='Run Hanabi AI experiments')
	parser.add_argument(
		'-n', '--num-runs',
		type=int,
		default=10,
		help='Number of runs per model (default: 10)'
	)
	parser.add_argument(
		'-o', '--output-dir',
		type=str,
		default='results',
		help='Output directory for results (default: results)'
	)
	
	args = parser.parse_args()
	
	run_experiments(args.num_runs, args.output_dir)


if __name__ == "__main__":
	main()
