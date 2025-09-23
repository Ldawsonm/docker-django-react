from typing import List, Dict
from abc import ABC, abstractmethod
from datetime import timedelta

class BaseScraper(ABC):
    """Abstract base class for all scrapers."""
    cutoff : timedelta = timedelta(days=30)

    def __init__(self, cutoff=timedelta(days=30)):
        self.cutoff = cutoff

    @abstractmethod
    def fetch_videos(self) -> List[Dict[str, str]]:
        """
        Must return a list of dicts with at least:
        { "title": str, "url": str }
        """
        pass
