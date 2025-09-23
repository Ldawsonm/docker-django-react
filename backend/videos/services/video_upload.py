import requests
from google.cloud import storage
from pathlib import Path

def upload_video_from_url(url: str, bucket_name: str, destination_blob_name: str):
    """
    Downloads an MP4 from a URL and uploads it to a GCS bucket.

    Args:
        url (str): The full HTTP/HTTPS URL of the MP4 file.
        bucket_name (str): Name of your GCS bucket.
        destination_blob_name (str): Path & filename in the bucket 
                                     (e.g. "house/video1.mp4").
    """
    # Initialize GCS client (will use GOOGLE_APPLICATION_CREDENTIALS env var or explicit credentials)
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Stream download to avoid loading the whole file into memory
    with requests.get(url, stream=True, verify=False) as r:
        r.raise_for_status()
        # Upload the streamed response directly to GCS
        blob.upload_from_file(r.raw, content_type="video/mp4")

    print(f"Uploaded {url} to gs://{bucket_name}/{destination_blob_name}")
