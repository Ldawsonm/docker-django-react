from google.cloud import storage_transfer
from datetime import datetime, timedelta

def transfer_http_to_gcs(http_url: str, bucket_name: str, destination_path: str):
    """
    Creates a Storage Transfer Service job to fetch a file from HTTP/HTTPS
    and store it in a GCS bucket.

    Args:
        http_url (str): Publicly accessible HTTP/HTTPS URL of the video.
        bucket_name (str): Target GCS bucket.
        destination_path (str): Path inside the bucket (e.g. "house/video.mp4").
    """

    client = storage_transfer.StorageTransferServiceClient()

    project_id = "direct-scheme-472916-d7"  # replace with your GCP project

    # Define when to run the transfer (must be "today" or future date)
    now = datetime.now()
    schedule = {
        "schedule_start_date": {"year": now.year, "month": now.month, "day": now.day},
        "schedule_end_date": {"year": now.year, "month": now.month, "day": now.day},
    }

    # Create transfer job
    transfer_job = {
        "project_id": project_id,
        "description": f"Fetch {http_url} into {bucket_name}/{destination_path}",
        "status": "ENABLED",
        "schedule": schedule,
        "transfer_spec": {
            "http_data_source": {"list_url": http_url},
            "gcs_data_sink": {"bucket_name": bucket_name, "path": destination_path},
        },
    }

    response = client.create_transfer_job({"transfer_job": transfer_job})
    print(f"Created transfer job: {response.name}")
