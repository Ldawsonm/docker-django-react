from datetime import datetime
from celery import shared_task, chain
from .models import Video, VideoStatus
from .utils.scrapers.mi_house import HouseScraper
from .utils.scrapers.mi_senate import SenateScraper

# from google.cloud.storage_transfer_v1 import types as st_types
from google.longrunning import operations_pb2

from google.cloud import storage_transfer_v1, storage, storage_transfer, videointelligence_v1 as vi


from google.api_core import operation
from google.cloud.videointelligence_v1 import AnnotateVideoResponse

import json
from django.utils import timezone

import logging
logger = logging.getLogger(__name__)

PROJECT_ID = "direct-scheme-472916-d7"
MANIFEST_BUCKET = "mi-vid-manifests"

@shared_task
def scrape_house():
    house_scraper = HouseScraper()
    house_videos = house_scraper.fetch_videos()
    # logger.info(house_videos)
    for video in house_videos:
        video, created = Video.objects.get_or_create(
            source_url=video["source_url"],
            defaults={"title": video["title"], "source": video["source"], "published_at": video["published_at"], "player_url": video["player_url"]},
        )
        print(f"successfully created or retrieved video object {video.id}")
        if created or video.status in [VideoStatus.NEW, VideoStatus.TRANSFER_FAILED, VideoStatus.TRANSCRIBE_FAILED]:
            # print(f"running transcription pipeline for video {video.id}")
            run_video_pipeline.delay(video.id)

@shared_task
def scrape_senate():
    senate_scraper = SenateScraper()
    senate_videos = senate_scraper.fetch_videos()
    for video in senate_videos:
        video, created = Video.objects.get_or_create(
            source_url=video["source_url"],
            defaults={"title": video["title"], "source": video["source"], "published_at": video["published_at"], "player_url": video["player_url"]},
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


@shared_task
def create_transfer_job(video_id: int):
    video = Video.objects.get(id=video_id)

    # Check if object already exists in GCS
    storage_client = storage.Client()
    bucket = storage_client.bucket(video.bucket)
    blob_path = f"{video.source}/{video.source_url}"
    blob = bucket.blob(blob_path)

    if blob.exists():
        video.status = VideoStatus.TRANSFER_DONE
        video.save()
        return video.id

    sts = storage_transfer.StorageTransferServiceClient()

    if video.sts_job_name:
        try:
            existing_job = sts.get_transfer_job(name=video.sts_job_name, project_id=PROJECT_ID)
            if existing_job:  # Job found
                video.status = VideoStatus.TRANSFERRING
                video.save()
                return video.id
        except Exception:
            # If job not found, continue to create a new one
            pass

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

@shared_task(bind=True, max_retries=30)
def poll_transfer_until_done(self, video_id):
    # logger.info(f"[poll_transfer_until_done] started for Video {video_id}")
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

    # op = client.annotate_video(
    #     request={
    #         "features": [vi.Feature.SPEECH_TRANSCRIPTION],
    #         "input_uri": f"gs://{video.bucket}/{video.source}/{video.gcs_object}",
    #         "video_context": vi.VideoContext(
    #             speech_transcription_config=vi.SpeechTranscriptionConfig(
    #                 language_code="en-US",
    #                 enable_automatic_punctuation=True,
    #             )
    #         ),
    #     }
    # )
    # video.vi_operation_name = op.operation.name
    # video.status = VideoStatus.TRANSCRIBING
    video.save()
    return video.id


@shared_task(bind=True, max_retries=60)
def poll_transcription_until_done(self, video_id):
    # logger.info(f"[poll_transcriptions_until_done] started for Video {video_id}")
    

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