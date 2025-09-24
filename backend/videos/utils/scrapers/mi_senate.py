from urllib.parse import urlparse, parse_qs


# import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
# from datetime import datetime, timedelta
from .base import BaseScraper
from ..date_parse import parse_date_from_title

import logging
logger = logging.getLogger(__name__)

API_URL = "https://tf4pr3wftk.execute-api.us-west-2.amazonaws.com/default/api/all"
api_id = "61b3adc8124d7d000891ca5c"

def fetch_page(page, results):
        payload = {"page": page, "results": results, "_id": api_id}
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://cloud.castus.tv",
            "referer": "https://cloud.castus.tv/",
            "user-agent": "Mozilla/5.0",
        }
        resp = requests.post(API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        # logger.info(data)
        return data.get("allFiles", [])  
source = "senate"

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

class SenateScraper(BaseScraper):
    
    

    def fetch_videos(self):
        # self.cutoff = datetime.now(timezone.utc) - self.cutoff

        max_pages = 10
        results_per_page=20

        # recent_videos = []
        cutoff = datetime.now(timezone.utc) - self.cutoff
        all_videos = []

        for page in range(1, max_pages + 1):
            files = fetch_page(page=page, results=results_per_page)
            # logger.info(files)
            if not files:
                break  # stop if empty page

            for item in files:
                # logger.info(item)
                date_str = item.get("date")
                if not date_str:
                    continue
                video_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if video_date < cutoff:
                    continue

                video_id = item["_id"]
                title = item.get("metadata", {}).get("filename", "Untitled")
                mp4_url = f"https://dlttx48mxf9m3.cloudfront.net/outputs/{video_id}/Default/MP4/out_1080.mp4"

                all_videos.append({
                    "title": title,
                    "source": source,
                    "published_at": video_date,
                    "source_url": mp4_url
                })

        return all_videos
        
        # page = 1

        # while page <= max_pages:
        #     resp = requests.post(
        #         API_URL,
        #         headers={"accept": "application/json"},
        #         params={"page": page, "results": results_per_page}
        #     )
        #     resp.raise_for_status()
        #     data = resp.json()

        #     if not data:  # No more results
        #         break

        #     logger.info(f"retrieved {len(data)} records on page {page}")

        #     for item in data:
        #         video_id = item["_id"]
        #         title = item.get("metadata", {}).get("filename", "Untitled")
        #         date_str = item.get("date")
        #         if not date_str:
        #             continue

        #         video_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

        #         if not video_date or video_date < self.cutoff:
        #             continue

        #         mp4_url = f"https://dlttx48mxf9m3.cloudfront.net/outputs/{video_id}/Default/MP4/out_1080.mp4"

        #         recent_videos.append({
        #             "title": title,
        #             "source": source,
        #             "published_at": video_date,
        #             "source_url": mp4_url
        #         })

        #     page += 1

        # return recent_videos

        # resp = requests.get(API_URL, headers={"accept": "application/json"})
        # resp.raise_for_status()
        # data = resp.json()

        

        # logger.info(f"retrieved {len(data)} records")

        # for item in data:
        #     video_id = item["_id"]
        #     title = item.get("metadata", {}).get("filename", "Untitled")
        #     date_str = item.get("date")

        #     # Parse the ISO8601 date string
        #     if not date_str:
        #         continue
        #     video_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

        #     # logger.info(f"video date is {video_date}")

        #     # Keep only videos newer than cutoff
        #     if not video_date or video_date < self.cutoff:
        #         continue
            
        #     # thumb_url = f"https://dlttx48mxf9m3.cloudfront.net/outputs/{video_id}/Default/Thumbnails/out_003.png"
        #     mp4_url = f"https://dlttx48mxf9m3.cloudfront.net/outputs/{video_id}/Default/MP4/out_1080.mp4"

        #     recent_videos.append({
        #         "title": title,
        #         "source": source,
        #         "published_at": video_date,
        #         "source_url": mp4_url
        #     })

        # return recent_videos