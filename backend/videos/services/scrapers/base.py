from typing import List, Dict
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    @abstractmethod
    def fetch_videos(self) -> List[Dict[str, str]]:
        """
        Must return a list of dicts with at least:
        { "title": str, "url": str }
        """
        pass
