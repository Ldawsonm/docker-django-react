import requests
from bs4 import BeautifulSoup

def scrape_video(url : str):
    url = "https://house.mi.gov/VideoArchive"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    videos = []
    for link in soup.select("a[href*='mp4']"):  # depends on actual structure
        videos.append({
            "title": link.text.strip(),
            "url": link["href"]
        })
    return videos
