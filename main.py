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


def get_base_link(provider: str) -> str:
	base_links = {
		"groq": "https://api.groq.com/openai/v1",
		"xai": "https://api.x.ai/v1"
	}
	if provider not in base_links:
		return None
	return base_links[provider]


def create_player(provider: str, model: str, args: Dict) -> object:
	PlayerClass = get_player_class(provider)
	
	# Get API key from environment variables
	api_key = os.getenv(f"{provider.upper()}_API_KEY")
	base_link = get_base_link(provider)

	if not api_key:
		raise ValueError(f"API key for {provider} not found in environment variables")
	
	if base_link:
		# add to args
		args["base_url"] = base_link

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
				"turns_played",
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
				players[1].debug = True # only print debug for the fourth player
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
					game.turns_played,
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
		'turns_played': ['mean']
	}).round(2)
	
	# Calculate win percentage (score of 25 is a win)
	win_games = latest_experiments[latest_experiments['score'] == 25].groupby(['provider', 'model', 'args']).size()
	total_games = latest_experiments.groupby(['provider', 'model', 'args']).size()
	win_pct = (win_games / total_games).fillna(0)  # Replace NaN with 0 when no wins
	
	summary['win_percentage'] = win_pct.round(2)
	
	# Flatten column names
	summary.columns = ['avg_score', 'std_score', 'num_games', 'win_percentage', 'avg_turns_played']

	# arrange by win_percentage, then by avg_score, then by avg_turns_played (higher is better for all)
	summary = summary.sort_values(by=['win_percentage', 'avg_score', 'avg_turns_played'], ascending=[False, False, False])
	
	# Save summary, overwrite if exists
	summary.reset_index().to_csv(summary_file, index=False)
	print(f"\nSummary saved to {summary_file}")


def main():
	parser = argparse.ArgumentParser(description='Hanabi AI experiments')
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
		help='Comma-separated list of models to run in the format: provider/model/{"args"}'
	)
	parser.add_argument(
		'-p', '--provider',
		type=str,
		default=None,
		help='Filter models by provider name'
	)
	parser.add_argument(
		'--only-new',
		action='store_true',
		help='Only run models that are not present in existing results'
	)
	parser.add_argument(
		'-d', '--debug',
		action='store_true',
		help='Enable debug mode'
	)
	
	parsed_args = parser.parse_args()
	
	models = []
	if parsed_args.models:
		for model in parsed_args.models.split(';'):
			provider, model, model_args = model.split('/')
			if model_args:
				model_args = json.loads(model_args)
			else:
				model_args = {"cot": 0}
			models.append({"provider": provider, "model": model, "args": model_args})
	else:
		models = AVAILABLE_MODELS  # run all models
	
	# Filter by provider if specified
	if parsed_args.provider:
		models = [m for m in models if m["provider"] == parsed_args.provider]
	
	# Filter out already tested models if only-new is specified
	if parsed_args.only_new and os.path.exists(os.path.join(parsed_args.output_dir, "experiment_results.csv")):
		df = pd.read_csv(os.path.join(parsed_args.output_dir, "experiment_results.csv"))
		tested_configs = set()
		for _, row in df.iterrows():
			config = f"{row['provider']}/{row['model']}/{row['args']}"
			tested_configs.add(config)
		
		models = [m for m in models if f"{m['provider']}/{m['model']}/{m['args']}" not in tested_configs]
	
	run_experiments(parsed_args.num_runs, parsed_args.output_dir, models, debug=parsed_args.debug)

if __name__ == "__main__":
	main()
