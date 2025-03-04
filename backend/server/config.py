import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = os.path.join(BASE_DIR, "data")
DEBATES_DIR = os.path.join(DATA_DIR, "debates")

# API Configuration
LLM_API_URL = os.environ.get("LLM_API_URL", "https://api.openai.com/v1/completions")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "your-api-key-here")
API_TIMEOUT = float(os.environ.get("API_TIMEOUT", "60.0"))

# Create required directories
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DEBATES_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
