import logging
import re
import time
from typing import List, Dict, Any, Optional
import json
import os
from abc import ABC, abstractmethod

from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)

# Constants
KIALO_BASE_URL = "https://www.kialo-edu.com/debate-topics-and-argumentative-essay-topics"
CACHE_DIR = "cache"  # Directory for storing cached data


class BaseScraper(ABC):
    """Base class for web scrapers."""

    def __init__(self):
        """Initialize the base scraper."""
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

    def _get(self, url: str) -> BeautifulSoup:
        """Get the HTML content of a URL and parse it with BeautifulSoup."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return BeautifulSoup(response.text, "html.parser")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching URL {url}: {e}")
            raise

    def save_data(self, data: Any, filename: str) -> None:
        """Save data to a JSON file in the cache directory."""
        filepath = os.path.join(CACHE_DIR, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving data to {filepath}: {e}")

    def load_data(self, filename: str) -> Optional[Any]:
        """Load data from a JSON file in the cache directory."""
        filepath = os.path.join(CACHE_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.info(f"Cache file not found: {filepath}")
            return None  # Explicitly return None
        except Exception as e:
            logger.error(f"Error loading data from {filepath}: {e}")
            return None

    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for debates."""
        pass

    @abstractmethod
    def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch a specific debate."""
        pass

    @abstractmethod
    def fetch_random_debates(self, count: int = 5) -> List[Dict[str, Any]]:
        """Fetch a number of random debates."""
        pass


class KialoScraper(BaseScraper):
    """Scraper for Kialo-Edu."""

    def __init__(self):
        """Initialize the Kialo scraper."""
        super().__init__()
        self.base_url = KIALO_BASE_URL
        self.debate_list_cache_file = "kialo_debate_list.json"  # Cache for the debate list
        self.debate_topics = self.load_debate_topics() # Load at startup

    def load_debate_topics(self) -> List[Dict[str, str]]:
        """Loads the debate topics from cache or scrapes them if not cached."""
        cached_topics = self.load_data(self.debate_list_cache_file)
        if cached_topics:
            logger.info(f"Loaded Kialo debate topics from cache.")
            return cached_topics
        else:
            logger.info("Scraping Kialo debate topics.")
            return self.scrape_debate_topics()


    def scrape_debate_topics(self) -> List[Dict[str, str]]:
        """Scrape the list of debate subjects from Kialo-Edu."""
        try:
            soup = self._get(self.base_url)
            debate_topics = []

            # Find all h2 elements, as they seem to contain the topics
            topic_elements = soup.find_all("h2")
            for topic_element in topic_elements:
                topic_text = topic_element.get_text(strip=True)
                if topic_text:
                    # Create a simple dict.  We don't have URLs here.
                    debate_topics.append({"title": topic_text, "url": "", "source": "kialo-edu.com"})

            self.save_data(debate_topics, self.debate_list_cache_file) # save
            return debate_topics

        except Exception as e:
            logger.error(f"Error scraping Kialo debate topics: {e}")
            return []


    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for debates on Kialo-Edu (within the scraped list)."""
        logger.info(f"Searching Kialo-Edu for: {query}")
        results = []

        for topic in self.debate_topics:
            if query.lower() in topic["title"].lower():
                results.append(topic)  # Append the entire topic dictionary

        return results


    def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch a specific debate from Kialo-Edu. Not applicable here, so return an informative dict."""
        logger.warning("Fetching individual debates by URL is not supported for Kialo-Edu in this scraper.")
        return {
            "title": "Not Supported",
            "url": url,
            "error": "Fetching individual debates by URL is not supported for this source.",
            "source": "kialo-edu.com"
        }


    def fetch_random_debates(self, count: int = 5) -> List[Dict[str, Any]]:
        """Fetch a number of random debate topics (not full debates) from the scraped list."""
        logger.info(f"Fetching {count} random debate topics from Kialo-Edu")
        import random

        # Ensure we don't try to sample more than we have
        count = min(count, len(self.debate_topics))
        selected_topics = random.sample(self.debate_topics, count)
        return selected_topics