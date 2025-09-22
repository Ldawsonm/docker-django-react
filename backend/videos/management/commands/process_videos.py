from django.core.management.base import BaseCommand
from videos.services.pipeline import process_scraper
from videos.services.scrapers.house import HouseScraper
from videos.services.scrapers.senate import SenateScraper

class Command(BaseCommand):
    help = "Scrape, download, and transcribe new videos"

    def handle(self, *args, **kwargs):
        process_scraper(HouseScraper(), "house")
        process_scraper(SenateScraper(), "senate")
