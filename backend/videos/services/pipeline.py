from moviepy import VideoFileClip
from videos.models import Video
from .downloader import download_video
from .converter import video_to_audio
from .transcriber import transcribe_video
from .cleaner import clean_video
from .video_upload import upload_video_from_url
from .transfer import transfer_http_to_gcs

def process_scraper(scraper, source_name: str):
    """
    Given a scraper, fetches new videos, downloads, and transcribes them.
    """
    new_videos = []

    # Step 1: Fetch
    for entry in scraper.fetch_videos():
        obj, created = Video.objects.get_or_create(
            url=entry["url"], file_name=entry["file_name"],
            defaults={"title": entry["title"], "source": source_name}
        )
        if created:
            new_videos.append(obj)
    
    # Step 2: Upload
    for video in Video.objects.filter(downloaded=False, source=source_name):
        try:
            # file_path = download_video(video.url)
            # video.local_path = file_path
            destination = f"{source_name}/"
            # upload_video_from_url(url=video.url, bucket_name="mi-vid-transcription", destination_blob_name=destination)
            transfer_http_to_gcs(
                http_url=video.url,
                bucket_name="mi-vid-transcription",
                destination_path=destination
            )
            video.downloaded = True
            video.save()
        except Exception as e:
            print(f"[ERROR] Upload failed for {video.url}: {e}")

    # Step 3: Transcribe
    for video in Video.objects.filter(transcribed=False, source=source_name):
        video_path = f"gs://mi-vid-transcription/{source_name}/{video.file_name}"
        transcription = transcribe_video(video_path)
        video.transcript = transcription
        video.save()


    # # Step 2: Download
    # for video in Video.objects.filter(downloaded=False, source=source_name):
    #     try:
    #         file_path = download_video(video.url)
    #         video.local_path = file_path
    #         video.downloaded = True
    #         video.save()
    #     except Exception as e:
    #         print(f"[ERROR] Download failed for {video.url}: {e}")

    # # Step 3: Transcribe
    # for video in Video.objects.filter(downloaded=True, transcribed=False, source=source_name):
    #     try:
    #         audio_file_path = video_to_audio(video.local_path)
    #         video.audio_file_path = audio_file_path
    #         text = transcribe_audio(audio_file_path)
    #         video.transcript = text
    #         video.transcribed = True
    #         video.save()
    #     except Exception as e:
    #         print(f"[ERROR] Transcription failed for {video.local_path}: {e}")

    # # Step 4: Remove the video and audio files
    # for video in Video.objects.filter(downloaded=True, cleaned=False, source=source_name):
    #     try:
    #         clean_video(video.local_path, video.audio_file_path)
    #         video.cleaned = True
    #         video.save()
    #     except Exception as e:
    #         print(f"[ERROR] Failed to remove files {video.local_path} and {video.audio_file_path}: {e}")
