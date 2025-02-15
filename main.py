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
from config.models import AVAILABLE_MODELS
import json

# Load environment variables from .env file
load_dotenv()

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


def run_experiments(
		num_runs: int, 
		output_dir: str = "results", 
		models: List[Dict] = AVAILABLE_MODELS,
		debug: bool = False
	):
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
				"hands_played",
				"score"
			])
	
	experiment_id = 1
	if os.path.exists(results_file):
		df = pd.read_csv(results_file)
		if not df.empty:
			experiment_id = df['experiment_id'].max() + 1
	
	# Run experiments for each model
	for model_config in models:
		provider = model_config["provider"]
		model_name = model_config["model"]
		args = model_config["args"]
		num_players = 5
		
		print(f"\n\nRunning {num_runs} games for {provider} - {model_name} with args {args}")
		
		for run in range(num_runs):
			print(f"Run {run + 1}/{num_runs} {provider} - {model_name} with args {args} -------------------------------")
			
			# Create player and game
			players = [create_player(provider, model_name, args) for _ in range(num_players)]
			if debug:
				players[0].debug = True # only print debug for the first player
			game = HanabiGame(players)
			
			# Run game and get score
			score = game.play_game(verbosity=1)
			
			# Save results
			with open(results_file, 'a', newline='') as f:
				writer = csv.writer(f)
				writer.writerow([
					experiment_id,
					provider,
					model_name,
					str(args),  # Convert dict to string for CSV storage
					datetime.now().isoformat(),
					game.hands_played,
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
	latest_experiments = df.sort_values('timestamp').groupby(['provider', 'model', 'args']).last()
	
	# Calculate summary statistics on latest experiments only
	summary = latest_experiments.groupby(['provider', 'model', 'args']).agg({
		'score': ['mean', 'std', 'count'],
		'hands_played': ['mean', 'std', 'count']
	}).round(2)
	
	# Calculate win percentage (score of 25 is a win)
	win_pct = latest_experiments[latest_experiments['score'] == 25].groupby(['provider', 'model', 'args']).size() / \
			  latest_experiments.groupby(['provider', 'model', 'args']).size() * 100
	
	summary['win_percentage'] = win_pct.round(2)
	
	# Flatten column names
	summary.columns = ['avg_score', 'std_score', 'num_games', 'win_percentage', 'avg_hands_played']
	
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
	parser.add_argument(
		'-m', '--models',
		type=str,
		default=None,
		help='Comma-separated list of models to run in the format: provider:model:[Optional args], e.g. openai:gpt-4o-mini-2024-07-18:{"cot": 1}'
	)
	parser.add_argument(
		'-d', '--debug',
		action='store_true',
		help='Enable debug mode'
	)
	
	args = parser.parse_args()
	
	models = []
	if args.models:
		for model in args.models.split(','):
			provider, model, args = model.split(':')
			if args:
				args = json.loads(args)
			else:
				args = {"cot": 0} # default args
			models.append({"provider": provider, "model": model, "args": args})
	else:
		models = AVAILABLE_MODELS # run all models
	
	run_experiments(args.num_runs, args.output_dir, models, debug=args.debug)

if __name__ == "__main__":
	main()
