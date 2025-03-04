import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import json

import requests
from bs4 import BeautifulSoup

from config import DATA_DIR

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base scraper class for all data sources."""
    
    def __init__(self):
        """Initialize the scraper."""
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.session.headers.update(self.headers)
        
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(DATA_DIR, self.__class__.__name__.lower())
        os.makedirs(self.data_dir, exist_ok=True)
        
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def _get(self, url: str) -> BeautifulSoup:
        """Make a GET request and return BeautifulSoup object."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            raise
    
    def save_data(self, data: Any, filename: str) -> str:
        """Save scraped data to a file."""
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved data to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving data to {filepath}: {e}")
            raise
    
    def load_data(self, filename: str) -> Any:
        """Load scraped data from a file."""
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded data from {filepath}")
            return data
        except FileNotFoundError:
            logger.warning(f"File not found: {filepath}")
            return None
        except Exception as e:
            logger.error(f"Error loading data from {filepath}: {e}")
            raise
    
    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for debates/topics based on a query."""
        pass
    
    @abstractmethod
    def fetch(self, url_or_id: str) -> Dict[str, Any]:
        """Fetch a specific debate/topic."""
        pass