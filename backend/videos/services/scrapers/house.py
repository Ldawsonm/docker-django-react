# import requests, certifi
# from bs4 import BeautifulSoup
# from .base import BaseScraper

# class HouseScraper(BaseScraper):
#     def fetch_videos(self):
#         url = "https://house.mi.gov/VideoArchive"
#         # session = requests.Session()
#         ## TODO FIX THIS!!!!
#         resp = requests.get(url, verify=False)
#         print(resp.status_code)
#         soup = BeautifulSoup(resp.text, "html.parser")

#         root = "https://house.mi.gov"

#         results = []
#         for link in soup.select("a[href*='.mp4']"):
#             results.append({
#                 "title": link.text.strip(),
#                 "url": root + link["href"]
#             })
#         return results
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .base import BaseScraper

class HouseScraper(BaseScraper):
    def fetch_videos(self):
        url = "https://house.mi.gov/VideoArchive"
        resp = requests.get(url, verify=False)
        print(resp.status_code)
        soup = BeautifulSoup(resp.text, "html.parser")

        root = "https://house.mi.gov/ArchiveVideoFiles/"
        results = []

        one_month_ago = datetime.now() - timedelta(days=30)

        for link in soup.select("a[href*='.mp4']"):
            title = link.text.strip()
            link_end = link["href"].split("=")[1] ## TODO Make less insecure
            video_url = root + link_end

            try:
                # Extract date-like substring, e.g., "September 8th, 2025"
                match = re.search(r"([A-Za-z]+ \d{1,2}(st|nd|rd|th)?, \d{4})", title)
                if not match:
                    continue

                raw_date = match.group(1)

                # Remove ordinal suffixes (st, nd, rd, th)
                clean_date = re.sub(r"(\d{1,2})(st|nd|rd|th)", r"\1", raw_date)

                # Parse into datetime
                date_obj = datetime.strptime(clean_date, "%B %d, %Y")

                # Only include videos newer than one month
                if date_obj >= one_month_ago:
                    results.append({
                        "title": title,
                        "url": video_url,
                        "date": date_obj
                    })

            except Exception as e:
                print(f"Skipping {title}: {e}")

        return results
