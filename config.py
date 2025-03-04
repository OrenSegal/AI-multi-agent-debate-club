import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenRouter configuration
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
OPENROUTER_MODEL_2 = os.getenv("OPENROUTER_MODEL_2")


# Web scraping configuration
WIKI_SEARCH_LIMIT = 5  # Number of Wikipedia articles to fetch per search

# Fallacy detection configuration
FALLACY_DETECTION_THRESHOLD = 0.7  # Confidence threshold for fallacy detection

# Agent parameters
MAX_TURNS_PER_DEBATE = 6  # Maximum number of turns per debate

# Path configurations
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Logging configuration
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(DATA_DIR, "debate_club.log"))
    ]
)
logger = logging.getLogger(__name__)