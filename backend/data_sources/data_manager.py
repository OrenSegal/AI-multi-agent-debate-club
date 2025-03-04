import os
import random
import requests
import polars as pl
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import wikipedia
import re
import time
import chromadb
from chromadb.config import Settings


class DataManager:
    """Manages data operations like topic retrieval and vectorized storage."""

    def __init__(self):
        self.topics_cache_file = "topics_cache.json"  # File to store scraped topics
        self.topics_cache = []
        self.index_name = "debate-topics"
        self.persist_directory = "db"  # Directory to persist ChromaDB data
        self.client = None
        self.collection = None

        # Initialize ChromaDB
        try:
            # Use persistent client to store data on disk
            self.client = chromadb.PersistentClient(path=self.persist_directory)

            # Get or create the collection
            self.collection = self.client.get_or_create_collection(name=self.index_name)

        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")

        self._load_topics_cache()  # Load cached topics on startup


    def get_available_topics(self) -> List[str]:
        """Get a list of available debate topics."""
        if self.topics_cache:
            return self.topics_cache

        try:
            # Try to scrape topics from Kialo Edu
            topics = self._scrape_kialo_topics()
            if topics:
                self.topics_cache = topics
                self._save_topics_cache()  # Save scraped topics
                return topics

        except Exception as e:
            print(f"Error scraping topics: {e}")

        # Fallback to a small list of general debate topics (same as before)
        fallback_topics = [
            "Should universal basic income be implemented?",
            "Is artificial intelligence a threat to humanity?",
            "Should college education be free?",
            "Is climate change primarily caused by human activities?",
            "Should vaccines be mandatory?",
            "Is social media harmful to society?",
            "Should gene editing of human embryos be legal?",
            "Is capitalism the best economic system?",
            "Should voting be mandatory?",
            "Is nuclear energy the solution to climate change?"
        ]

        self.topics_cache = fallback_topics
        self._save_topics_cache() # Save fallback topics
        return fallback_topics


    def _scrape_kialo_topics(self) -> List[str]:
        """Scrape debate topics from kialo-edu.com."""
        topics = []
        url = "https://www.kialo-edu.com/debate-topics-and-argumentative-essay-topics"

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; DebateClubBot/1.0; +http://example.com/bot)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            soup = BeautifulSoup(response.text, "html.parser")

            # Find all list items within <ul> tags, targeting the structure of the Kialo page
            list_items = soup.find_all('li')

            for li in list_items:
                topic_text = li.text.strip()
                # Basic filtering and formatting
                if topic_text and len(topic_text) > 10:  # Ensure it's a reasonable length
                    formatted_topic = self._format_topic_as_question(topic_text)
                    if formatted_topic not in topics: # Avoid adding duplicates
                        topics.append(formatted_topic)

        except Exception as e:
            print(f"Error scraping Kialo topics: {e}")

        return topics

    def _format_topic_as_question(self, topic: str) -> str:
        """Format a topic as a debate question if it isn't already."""
        topic = topic.strip()
        if topic.endswith('?'):
            return topic

        # Remove common prefixes if present
        prefixes = ['should', 'is', 'are', 'does', 'can', 'will', 'would']
        lower_topic = topic.lower()
        if any(lower_topic.startswith(prefix) for prefix in prefixes):
            return topic.capitalize() + '?'

        # Add 'Should' prefix for statements
        return f"Should {topic.lower()}?"


    def _load_topics_cache(self):
        """Load topics from the cache file."""
        try:
            if os.path.exists(self.topics_cache_file):
                with open(self.topics_cache_file, "r") as f:
                    import json
                    self.topics_cache = json.load(f)
        except Exception as e:
            print(f"Error loading topics cache: {e}")

    def _save_topics_cache(self):
        """Save topics to the cache file."""
        try:
            with open(self.topics_cache_file, "w") as f:
                import json
                json.dump(self.topics_cache, f)
        except Exception as e:
            print(f"Error saving topics cache: {e}")

    def get_random_topic(self) -> str:
        """Get a random debate topic."""
        topics = self.get_available_topics()
        return random.choice(topics) if topics else "Should artificial intelligence be regulated?"

    def get_topic_background(self, topic: str) -> str:
        """Get background information on a topic from Wikipedia and other sources."""
        background_info = ""

        # Try to get information from Wikipedia
        try:
            # Clean topic for Wikipedia search
            clean_topic = re.sub(r'[Ss]hould\s|[Ii]s\s|[Aa]re\s|[Dd]oes\s', '', topic)
            clean_topic = clean_topic.rstrip('?')

            # Search Wikipedia
            search_results = wikipedia.search(clean_topic, results=3)

            if search_results:
                try:
                    # Try to get the most relevant page
                    page = wikipedia.page(search_results[0], auto_suggest=False)
                    summary = page.summary
                    background_info = f"From Wikipedia: {summary}\n\n"
                except wikipedia.exceptions.DisambiguationError as e:
                    # If disambiguation, try the first option
                    if e.options:
                        try:
                            page = wikipedia.page(e.options[0], auto_suggest=False)
                            summary = page.summary
                            background_info = f"From Wikipedia: {summary}\n\n"
                        except:
                            pass
                except:
                    # If first result fails, try the second
                    if len(search_results) > 1:
                        try:
                            page = wikipedia.page(search_results[1], auto_suggest=False)
                            summary = page.summary
                            background_info = f"From Wikipedia: {summary}\n\n"
                        except:
                            pass
        except Exception as e:
            print(f"Error getting Wikipedia info: {e}")

        # If no Wikipedia info is found, provide a generic message
        if not background_info:
            background_info = ("No specific background information found. "
                               "The debaters should rely on their knowledge of the topic.")

        return background_info
    def save_debate_to_storage(self, debate_data: Dict[str, Any]) -> bool:
        """Save a completed debate to vector storage (ChromaDB) for future reference."""
        if not self.collection:
            return False

        try:
            from langchain_openai import OpenAIEmbeddings

            # Create a combined text representation of the debate
            debate_text = f"Topic: {debate_data['topic']}\n"
            debate_text += f"Introduction: {debate_data['introduction']}\n\n"

            for i, round_data in enumerate(debate_data['rounds']):
                debate_text += f"Round {i+1}:\n"
                debate_text += f"Pro: {round_data.get('pro_argument', '')}\n"
                debate_text += f"Con: {round_data.get('con_argument', '')}\n\n"

            debate_text += f"Pro Conclusion: {debate_data.get('pro_conclusion', '')}\n"
            debate_text += f"Con Conclusion: {debate_data.get('con_conclusion', '')}\n"
            debate_text += f"Evaluation: {debate_data.get('evaluation', '')}\n"


            # Create embedding
            embeddings = OpenAIEmbeddings()
            vector = embeddings.embed_query(debate_text)

            # Save to ChromaDB
            self.collection.add(
                embeddings=[vector],
                documents=[debate_text],
                metadatas=[debate_data],
                ids=[debate_data['topic']]  # Use topic as a unique ID
            )
            return True

        except Exception as e:
            print(f"Error saving to vector store: {e}")
            return False