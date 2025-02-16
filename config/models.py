BASE_MODELS = [
	# OpenAI models
	{"provider": "openai", "model": "gpt-4o-2024-08-06"},
	{"provider": "openai", "model": "gpt-4o-mini-2024-07-18"},
	{"provider": "openai", "model": "o1-2024-12-17"},
	{"provider": "openai", "model": "o1-mini-2024-09-12"},
	{"provider": "openai", "model": "o3-mini-2025-01-31"},
	
	# Anthropic models
	{"provider": "anthropic", "model": "claude-3-sonnet-20240229"},
	{"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
	{"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
	{"provider": "anthropic", "model": "claude-3-haiku-20240307"},
	{"provider": "anthropic", "model": "claude-3-opus-20240229"},
	
	# Google models
	{"provider": "google", "model": "gemini-2.0-flash"},
	{"provider": "google", "model": "gemini-2.0-flash-lite-preview-02-05"},
	{"provider": "google", "model": "gemini-1.5-flash"},
	{"provider": "google", "model": "gemini-1.5-flash-8b"},
	{"provider": "google", "model": "gemini-1.5-pro"},
	
	# Groq models
	{"provider": "groq", "model": "mixtral-8x7b-32768"},
	{"provider": "groq", "model": "gemma2-9b-it"},
	{"provider": "groq", "model": "llama-3.3-70b-versatile"},
	{"provider": "groq", "model": "llama-3.1-8b-instant"},
	{"provider": "groq", "model": "llama-guard-3-8b"},
	{"provider": "groq", "model": "llama3-70b-8192"},
	{"provider": "groq", "model": "llama3-8b-8192"},
	{"provider": "groq", "model": "deepseek-r1-distill-llama-70b"},
	{"provider": "groq", "model": "deepseek-r1-distill-qwen-32b"},
	{"provider": "groq", "model": "qwen-2.5-32b"},
	
	# XAI models
	{"provider": "xai", "model": "grok-2-1212"},
	
	# Test models
	{"provider": "test", "model": "random"}
]


def generate_model_variations():
	all_models = []
	
	for base_model in BASE_MODELS:
		provider = base_model["provider"]
		model = base_model["model"]
		
		if provider == "openai" and model.startswith("o"):
			# For OpenAI "o" models, generate variations with different reasoning efforts
			reasoning_efforts = ["low", "medium", "high"]
			for effort in reasoning_efforts:
				for cot in [0, 1]:
					all_models.append({
						"provider": provider,
						"model": model,
						"args": {
							"cot": cot,
							"reasoning_effort": effort
						}
					})
		elif provider == "test":
			# Test models only need one version
			all_models.append({
				"provider": provider,
				"model": model,
				"args": {"cot": 0}
			})
		else:
			# For all other models, generate cot:0 and cot:1 versions
			for cot in [0, 1]:
				all_models.append({
					"provider": provider,
					"model": model,
					"args": {"cot": cot}
				})
	
	return all_models


AVAILABLE_MODELS = generate_model_variations() 