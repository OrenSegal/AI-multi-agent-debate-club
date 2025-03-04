import logging
from typing import List, Dict, Any, Optional
import re
import time

import wikipedia

from data_sources.scraper import BaseScraper
from config import WIKI_SEARCH_LIMIT

logger = logging.getLogger(__name__)


class WikipediaScraper(BaseScraper):
    """Scraper for Wikipedia."""
    
    def __init__(self):
        """Initialize the Wikipedia scraper."""
        super().__init__()
        # Set Wikipedia language to English
        wikipedia.set_lang("en")
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for topics on Wikipedia."""
        # First check if we have cached results
        cache_filename = f"wiki_search_{re.sub(r'[^\w]', '_', query.lower())}.json"
        cached_results = self.load_data(cache_filename)
        if cached_results:
            return cached_results
        
        logger.info(f"Searching Wikipedia for: {query}")
        
        try:
            # Search Wikipedia for the query
            search_results = wikipedia.search(query, results=WIKI_SEARCH_LIMIT)
            
            results = []
            for title in search_results:
                try:
                    # Get summary of the page
                    summary = wikipedia.summary(title, sentences=3)
                    url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                    
                    results.append({
                        "title": title,
                        "url": url,
                        "summary": summary,
                        "source": "wikipedia.org"
                    })
                except wikipedia.exceptions.DisambiguationError as e:
                    # Handle disambiguation pages
                    logger.info(f"Disambiguation for {title}: {e.options}")
                    for option in e.options[:2]:  # Limit to first 2 options
                        try:
                            option_summary = wikipedia.summary(option, sentences=2)
                            option_url = f"https://en.wikipedia.org/wiki/{option.replace(' ', '_')}"
                            
                            results.append({
                                "title": option,
                                "url": option_url,
                                "summary": option_summary,
                                "source": "wikipedia.org"
                            })
                        except Exception as inner_e:
                            logger.warning(f"Error getting summary for {option}: {inner_e}")
                except Exception as e:
                    logger.warning(f"Error getting summary for {title}: {e}")
            
            # Save results to cache
            self.save_data(results, cache_filename)
            
            return results
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {e}")
            return []
    
    def fetch(self, title_or_url: str) -> Dict[str, Any]:
        """Fetch a specific topic from Wikipedia."""
        # Extract title from URL if needed
        if title_or_url.startswith("http"):
            title = title_or_url.split("/wiki/")[-1].replace("_", " ")
        else:
            title = title_or_url
        
        # Generate a filename from the title
        cache_filename = f"wiki_{re.sub(r'[^\w]', '_', title.lower())}.json"
        
        # Check if we have cached data
        cached_data = self.load_data(cache_filename)
        if cached_data:
            return cached_data
        
        logger.info(f"Fetching Wikipedia article: {title}")
        
        try:
            # Get page content
            page = wikipedia.page(title)
            
            # Process content
            content = page.content
            url = page.url
            
            # Extract sections
            sections = []
            for section in content.split("== "):
                if " ==" in section:
                    section_title, section_content = section.split(" ==", 1)
                    sections.append({
                        "title": section_title.strip(),
                        "content": section_content.strip()
                    })
            
            # Prepare data
            article_data = {
                "title": page.title,
                "url": url,
                "summary": wikipedia.summary(title, sentences=5),
                "content": content,
                "sections": sections,
                "references": page.references,
                "source": "wikipedia.org",
                "scraped_at": time.time()
            }
            
            # Save article data to cache
            self.save_data(article_data, cache_filename)
            
            return article_data
        except wikipedia.exceptions.DisambiguationError as e:
            logger.warning(f"Disambiguation error for {title}: {e.options}")
            return {
                "title": title,
                "error": "Disambiguation error",
                "options": e.options,
                "source": "wikipedia.org"
            }
        except Exception as e:
            logger.error(f"Error fetching Wikipedia article: {e}")
            return {
                "title": title,
                "error": str(e),
                "source": "wikipedia.org"
            }
    
    def fetch_related(self, title: str, count: int = 3) -> List[Dict[str, Any]]:
        """Fetch related topics based on a Wikipedia article."""
        logger.info(f"Fetching topics related to {title} from Wikipedia")
        
        try:
            # Search for related topics
            related_titles = wikipedia.search(title, results=count+1)
            # Remove the original topic if present
            related_titles = [t for t in related_titles if t.lower() != title.lower()][:count]
            
            related_data = []
            for related_title in related_titles:
                article = self.fetch(related_title)
                if "error" not in article:
                    related_data.append({
                        "title": article["title"],
                        "url": article["url"],
                        "summary": article["summary"],
                        "source": "wikipedia.org"
                    })
            
            return related_data
        except Exception as e:
            logger.error(f"Error fetching related topics: {e}")
            return []