# core/tasks.py
# import re
# import requests
# from bs4 import BeautifulSoup
from datetime import datetime
from celery import shared_task, chain
from .models import Video, VideoStatus
from utils.scrapers.mi_house import HouseScraper

from google.cloud.storage_transfer_v1 import types as st_types
from google.longrunning import operations_pb2

from google.cloud import storage_transfer, videointelligence_v1 as vi
from celery import shared_task
from .models import Video, VideoStatus
from django.conf import settings
from datetime import datetime

from google.cloud import storage_transfer
from google.cloud import storage
from datetime import datetime
from .models import Video, VideoStatus

from google.cloud import storage_transfer_v1


from google.api_core import operation
from google.cloud.videointelligence_v1 import AnnotateVideoResponse

import json

from celery import shared_task
from django.utils import timezone
from .models import Video, VideoStatus

import logging
logger = logging.getLogger(__name__)

PROJECT_ID = "direct-scheme-472916-d7"
MANIFEST_BUCKET = "mi-vid-manifests"

# HOUSE_URL = "https://house.mi.gov/VideoArchive"
# SENATE_URL = "https://cloud.castus.tv/vod/misenate/?page=ALL"

# DATE_RE = re.compile(
#     r"(?:[A-Za-z]+,\s*)?"           # optional weekday like "Tuesday, "
#     r"([A-Za-z]+)\s+"               # month name or abbr (captured)
#     r"(\d{1,2})(?:st|nd|rd|th)?\s*" # day number with optional suffix
#     r",?\s*"                        # optional comma
#     r"(\d{4})"                      # year
# )

# from urllib.parse import urlparse, parse_qs

# HOUSE_VIDEO_ROOT = "https://www.house.mi.gov/ArchiveVideoFiles/"
# SENATE_VIDEO_ROOT = "https://www.senate.michigan.gov/ArchiveVideoFiles/"  # example

# def resolve_video_url(href: str, source: str) -> str | None:
#     """
#     Convert archive player links into direct MP4 file links.
#     """
#     parsed = urlparse(href)

#     # Case 1: It’s a player link with ?video= param
#     if parsed.path.endswith("VideoArchivePlayer"):
#         qs = parse_qs(parsed.query)
#         if "video" in qs:
#             filename = qs["video"][0]
#             base = HOUSE_VIDEO_ROOT if source == "house" else SENATE_VIDEO_ROOT
#             return f"{base}{filename}"

#     # Case 2: Already a raw MP4 link
#     if parsed.path.endswith(".mp4"):
#         return href if href.startswith("http") else f"https://{parsed.netloc}{parsed.path}"

#     # Fallback: unsupported href
#     return None


# def parse_date_from_title(title: str) -> datetime | None:
#     # Normalize any weird spaces (NBSP)
#     title = title.replace("\xa0", " ")
#     m = DATE_RE.search(title)
#     if not m:
#         return None

#     month_raw, day, year = m.groups()
#     # Strip trailing dot on abbreviations (e.g., "Sept.")
#     month = month_raw.rstrip(".")

#     # Try full month first (September), then abbreviated (Sep)
#     for fmt in ("%B %d %Y", "%b %d %Y"):
#         try:
#             return datetime.strptime(f"{month} {day} {year}", fmt)
#         except ValueError:
#             continue
#     return None

# def parse_date_with_suffix(text: str):
#     # Remove weekday if present
#     text = re.sub(r"^[A-Za-z]+,\s+", "", text)  # drop "Thursday, "
#     # Remove suffixes like "st", "nd", "rd", "th"
#     text = re.sub(r"(\d{1,2})(st|nd|rd|th)", r"\1", text)
#     try:
#         return datetime.strptime(text.strip(), "%B %d, %Y")
#     except ValueError:
#         return None

@shared_task
def scrape_sources():
    # cutoff = datetime.now() - timedelta(days=30)
    # for source, url in (("house", HOUSE_URL), ("senate", SENATE_URL)):
    # for i in range(1):
    #     source = "house"
    #     url = HOUSE_URL
    #     resp = requests.get(url, timeout=30, verify=False)
    #     resp.raise_for_status()
    #     soup = BeautifulSoup(resp.text, "html.parser")
        # print("fetched the page")
    
        # for link in soup.select("a[href*='.mp4']"):
            # title = link.text.strip()
            # href = link["href"]
            # video_url = resolve_video_url(href, source)
            # if not video_url:
            #     continue  # skip if can't resolve


            # # print(f"found video {title} with link {video_url}")

            # # extract date if present
            # published_at = parse_date_from_title(title)
            # if not published_at or published_at < cutoff:
            #     # print(f"video published at {published_at}. Skipping this.")
            #     continue
    house_scraper = HouseScraper()
    house_videos = house_scraper.fetch_videos()
    for video in house_videos:
        video, created = Video.objects.get_or_create(
            source_url=video["source_url"],
            defaults={"title": video["title"], "source": video["source"], "published_at": video["published_at"]},
        )
        # print(f"successfully created or retrieved video object {video.id}")
        if created or video.status in [VideoStatus.NEW, VideoStatus.TRANSFER_FAILED, VideoStatus.TRANSCRIBE_FAILED]:
            # print(f"running transcription pipeline for video {video.id}")
            run_video_pipeline.delay(video.id)





@shared_task(bind=True)
def run_video_pipeline(self, video_id):
    """Kick off the pipeline chain for a single video."""
    chain(
        create_transfer_job.s(video_id),
        poll_transfer_until_done.s(),
        start_transcription.s(),
        poll_transcription_until_done.s(),
    )()





def create_manifest_file(video: Video) -> str:
    """Create a manifest TSV file in GCS and return its URI."""
    client = storage.Client()
    bucket = client.bucket(MANIFEST_BUCKET)

    filename = f"{video.source}_{video.id}.tsv"
    blob = bucket.blob(filename)

    manifest = "TsvHttpData-1.0\n" + video.source_url + "\n"
    blob.upload_from_string(manifest, content_type="text/plain")

    blob.acl.all().grant_read()
    blob.acl.save()

    return f"gs://{MANIFEST_BUCKET}/{filename}"

@shared_task
def create_transfer_job(video_id: int):
    video = Video.objects.get(id=video_id)
    sts = storage_transfer.StorageTransferServiceClient()

    manifest_uri = create_manifest_file(video)

    now = datetime.now()
    job = {
        "project_id": PROJECT_ID,
        "transfer_spec": {
            "http_data_source": {"list_url": manifest_uri},  # NOTE: GCS path to TSV
            "gcs_data_sink": {"bucket_name": video.bucket, "path": f"{video.source}/"},
        },
        "status": "ENABLED",
        "schedule": {
            "schedule_start_date": {"year": now.year, "month": now.month, "day": now.day},
            "schedule_end_date": {"year": now.year, "month": now.month, "day": now.day},
        },
    }

    created = sts.create_transfer_job({"transfer_job": job})
    sts.run_transfer_job({"project_id": PROJECT_ID, "job_name": created.name})

    video.sts_job_name = created.name
    video.status = VideoStatus.TRANSFERRING
    video.save()
    return video.id



def remove_url_prefix(url: str) -> str:
    if url.startswith("https://"):
        return url.removeprefix("https://")
    elif url.startswith("http://"):
        return url.removeprefix("http://")
    return url

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=30)
def poll_transfer_until_done(self, video_id):
    logger.info(f"[poll_transfer_until_done] started for Video {video_id}")
    video = Video.objects.get(id=video_id)
    client = storage_transfer_v1.StorageTransferServiceClient()


    filter_obj = {
        "project_id": PROJECT_ID,
        "job_names": [video.sts_job_name],
    }
    filter_str = json.dumps(filter_obj)

    request = operations_pb2.ListOperationsRequest(
        filter=filter_str
    )

    ops_resp = client.list_operations(request=request)
    ops = list(ops_resp.operations)
    # logger.info(f"ops is {ops} ops 0 is {ops[0]}")
    if ops and ops[0].done:
        # logger.info(f"Here is the Operation: {ops[0]}")
        video.status = VideoStatus.TRANSFER_DONE
        video.gcs_object = remove_url_prefix(video.source_url)
        video.save()
        # logger.info(f"VI OPERATION NAME IS {video.vi_operation_name}. {None} for control")
        # if not video.vi_operation_name:
        #     start_transcription(video_id=video.id)
        return video.id
    raise Exception("Transfer not done yet")

@shared_task(bind=True)
def start_transcription(self, video_id):
    video = Video.objects.get(id=video_id)
    client = vi.VideoIntelligenceServiceClient()

    video.gcs_object = remove_url_prefix(video.source_url)

    op = client.annotate_video(
        request={
            "features": [vi.Feature.SPEECH_TRANSCRIPTION],
            "input_uri": f"gs://{video.bucket}/{video.source}/{video.gcs_object}",
            "video_context": vi.VideoContext(
                speech_transcription_config=vi.SpeechTranscriptionConfig(
                    language_code="en-US",
                    enable_automatic_punctuation=True,
                )
            ),
        }
    )
    video.vi_operation_name = op.operation.name
    video.status = VideoStatus.TRANSCRIBING
    video.save()
    return video.id


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=60)
def poll_transcription_until_done(self, video_id):
    logger.info(f"[poll_transcriptions_until_done] started for Video {video_id}")
    

    video = Video.objects.get(id=video_id)
    client = vi.VideoIntelligenceServiceClient(transport="grpc")

    # Use the transport’s operations_client to fetch the raw operation
    raw_op = client.transport.operations_client.get_operation(
    name=video.vi_operation_name
)

    # Wrap it into a convenient Operation object
    op = operation.from_gapic(
        raw_op,
        client.transport.operations_client,
        vi.AnnotateVideoResponse,
        metadata_type=vi.AnnotateVideoProgress,
    )
    if not op.done:
        raise Exception("Transcription not done yet")

    if op.exception():
        video.status = VideoStatus.TRANSCRIBE_FAILED
        video.error_message = str(op.exception())
        video.save()
        return video.id

    result = op.result()  # AnnotateVideoResponse

    transcript = []
    for st in result.annotation_results[0].speech_transcriptions:
        for alt in st.alternatives:
            transcript.append(alt.transcript)

    video.transcript_text = "\n".join(transcript)
    video.status = VideoStatus.COMPLETE
    video.save()

    return video.id



@shared_task
def sweep_in_progress_transfers():
    """
    Periodic task: find any videos stuck in TRANSFERRING and re-check their transfer job.
    """
    in_progress = Video.objects.filter(status=VideoStatus.TRANSFERRING)

    if not in_progress.exists():
        return "No transfers in progress"

    for video in in_progress:
        # Kick off a poll task for each
        poll_transfer_until_done.delay(video.id)

    return f"Scheduled {in_progress.count()} transfer polls at {timezone.now()}"

@shared_task
def sweep_in_progress_transcriptions():
    in_progress = Video.objects.filter(status=VideoStatus.TRANSCRIBING)
    for video in in_progress:
        poll_transcription_until_done.delay(video.id)

@shared_task
def sweep_pipeline():
    # Perform a filtered search with all statuses except complete
    videos_not_complete = Video.objects.exclude(status=VideoStatus.COMPLETE)
    for video in videos_not_complete:
        match video.status:
            case VideoStatus.NEW:
                logger.info(f"Video {video.id} is new. Starting Pipeline for video")
                run_video_pipeline.delay(video.id)
            case VideoStatus.TRANSFERRING:
                logger.info(f"Video {video.id} is transferring. Starting polling task.")
                poll_transfer_until_done.delay(video.id)
            case VideoStatus.TRANSFER_FAILED:
                run_video_pipeline.delay(video.id)
                logger.error(f"Transcription Failed for {video.id}. Restarting Pipeline for video")
            case VideoStatus.TRANSFER_DONE:
                logger.info(f"Video {video.id} is finished transferring. Starting Transcription")
                start_transcription.delay(video.id)
            case VideoStatus.TRANSCRIBING:
                logger.info(f"Video {video.id} is transcribing. Starting polling task.")
                poll_transcription_until_done.delay(video.id)
            case VideoStatus.TRANSCRIBE_FAILED:
                logger.error(f"Transcription Failed for {video.id}. Restarting Pipeline for video")
                run_video_pipeline.delay(video.id)
    logger.info("Completed pipeline sweep")
