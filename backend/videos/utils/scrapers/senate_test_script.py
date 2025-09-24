import requests

API_URL = "https://2kbyogxrg4.execute-api.us-west-2.amazonaws.com/61b3adc8124d7d000891ca5c/home/Senate%20Session"

def fetch_videos():
    resp = requests.get(API_URL, headers={"accept": "application/json"})
    resp.raise_for_status()
    data = resp.json()

    videos = []
    for item in data:
        video_id = item["_id"]
        title = item.get("metadata", {}).get("filename", "Untitled")
        date = item.get("date")

        # Build thumbnail and mp4 URLs from the pattern
        thumb_url = f"https://dlttx48mxf9m3.cloudfront.net/outputs/{video_id}/Default/Thumbnails/out_003.png"
        mp4_url = f"https://dlttx48mxf9m3.cloudfront.net/outputs/{video_id}/Default/MP4/out_1080.mp4"

        videos.append({
            "id": video_id,
            "title": title,
            "date": date,
            "thumbnail": thumb_url,
            "mp4": mp4_url
        })

    return videos

if __name__ == "__main__":
    videos = fetch_videos()
    for v in videos:
        print(f"{v['date']} - {v['title']}")
        print(f"  Thumbnail: {v['thumbnail']}")
        print(f"  MP4: {v['mp4']}")
        print()
