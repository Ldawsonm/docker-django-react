# import subprocess
# import yt_dlp
# from pathlib import Path

# def download_video(url: str, output_dir="downloads") -> str:
#     """
#     Downloads a video and returns the local file path.
#     """
#     Path(output_dir).mkdir(exist_ok=True)
#     # yt-dlp handles many formats robustly
#     result = subprocess.run(
#         ["yt-dlp", "-S", "+size,+br", "--no-check-certificates","-o", f"{output_dir}/%(title)s.%(ext)s", url],
#         capture_output=True, text=True
#     )
#     if result.returncode != 0:
#         raise RuntimeError(f"Download failed: {result.stderr}")
#     # yt-dlp prints path to stdout in verbose mode; you can also compute it
#     return output_dir
import requests
from pathlib import Path

# def download_video(url: str, output_dir="downloads") -> str:
#     """
#     Downloads a video using requests and saves it to output_dir.
#     Returns the local file path.
#     """
#     Path(output_dir).mkdir(exist_ok=True)

#     # Extract filename from URL or fall back to default
#     filename = url.split("/")[-1] or "video.mp4"
#     output_path = Path(output_dir) / filename

#     # Stream the video download
#     ## TODO FIX THE VERIFY
#     # Stream download the mp4
#     with requests.get(url, stream=True, verify=False) as r:
#         r.raise_for_status()
#         with open(output_path, "wb") as f:
#             for chunk in r.iter_content(chunk_size=8192):
#                 f.write(chunk)

#     return str(output_path)

# def download_video(url: str, output_dir="downloads") -> str:
#     """
#     Downloads a video and returns the local file path.
#     """
#     Path(output_dir).mkdir(exist_ok=True)
#     # yt-dlp handles many formats robustly
#     with yt_dlp.YoutubeDL({'extract_audio': True, 'format': 'bestaudio', 'outtmpl': '%(title)s.mp3'}) as video:
#         info_dict = video.extract_info(link, download = True)
#     # yt-dlp prints path to stdout in verbose mode; you can also compute it
#     return output_dir
import os
import requests
import subprocess

def download_video(url: str, output_dir: str = "downloads"):
    os.makedirs(output_dir, exist_ok=True)

    # Temporary mp4 file
    temp_mp4 = os.path.join(output_dir, "temp.mp4")
    # Final mp3 file
    mp3_path = os.path.join(output_dir, os.path.basename(url).rsplit(".", 1)[0] + ".mp3")

    # Stream download the mp4
    with requests.get(url, stream=True, verify=False) as r:
        r.raise_for_status()
        with open(temp_mp4, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    # Use ffmpeg to extract audio
    subprocess.run([
        "ffmpeg", "-y", "-i", temp_mp4, "-vn",  # -vn disables video
        "-acodec", "mp3", mp3_path
    ], check=True)

    # Clean up temp file
    os.remove(temp_mp4)

    return mp3_path
