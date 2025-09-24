from urllib.parse import urlparse, parse_qs


# import re
import requests
from bs4 import BeautifulSoup
# from datetime import datetime, timedelta
from datetime import datetime, timezone, timedelta
from .base import BaseScraper
from ..date_parse import parse_date_from_title

HOUSE_URL = "https://house.mi.gov/VideoArchive"
BASE_URL = "https://house.mi.gov"
HOUSE_VIDEO_ROOT = "https://www.house.mi.gov/ArchiveVideoFiles/"
source = "house"

def resolve_video_url(href: str) -> str | None:
    """
    Convert archive player links into direct MP4 file links.
    """
    parsed = urlparse(href)

    # Case 1: It’s a player link with ?video= param
    if parsed.path.endswith("VideoArchivePlayer"):
        qs = parse_qs(parsed.query)
        if "video" in qs:
            filename = qs["video"][0]
            base = HOUSE_VIDEO_ROOT
            return f"{base}{filename}"

    # Case 2: Already a raw MP4 link
    if parsed.path.endswith(".mp4"):
        return href if href.startswith("http") else f"https://{parsed.netloc}{parsed.path}"

    # Fallback: unsupported href
    return None

class HouseScraper(BaseScraper):
    
    def fetch_videos(self):
        cutoff = datetime.now(timezone.utc) - self.cutoff
        source = "house"
        url = HOUSE_URL
        resp = requests.get(url, timeout=30, verify=False)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # print("fetched the page")
        
        results = []

        for link in soup.select("a[href*='.mp4']"):
            title = link.text.strip()
            href = link["href"]
            player_url = f"{BASE_URL}{href}"
            video_url = resolve_video_url(href)
            # print(video_url)
            if not video_url:
                continue  # skip if can't resolve


            # print(f"found video {title} with link {video_url}")

            # extract date if present
            published_at = parse_date_from_title(title)
            if not published_at or published_at < cutoff:
                # print(f"video published at {published_at}. Skipping this.")
                continue
            vid_info = {
                "title": title,
                "source": source,
                "published_at": published_at,
                "source_url": video_url,
                "player_url": player_url
            }
            results.append(vid_info)
        return results