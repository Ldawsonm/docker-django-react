# from django.db import models

# # Create your models here.
# from django.db import models

# class VideoStatus(models.TextChoices):
#     NEW = "NEW", "Discovered"
#     TRANSFER_QUEUED = "TRANSFER_QUEUED", "Transfer queued"
#     TRANSFERRING = "TRANSFERRING", "Transferring"
#     TRANSFER_FAILED = "TRANSFER_FAILED", "Transfer failed"
#     TRANSFER_DONE = "TRANSFER_DONE", "Transfer complete"
#     TRANSCRIBE_QUEUED = "TRANSCRIBE_QUEUED", "Transcription queued"
#     TRANSCRIBING = "TRANSCRIBING", "Transcribing"
#     TRANSCRIBE_FAILED = "TRANSCRIBE_FAILED", "Transcription failed"
#     COMPLETE = "COMPLETE", "Complete"

# class Video(models.Model):
#     source = models.CharField(max_length=50)  # 'house' or 'senate'
#     title = models.CharField(max_length=255, default="")
#     url = models.URLField(unique=True)
#     local_path = models.CharField(max_length=255, default="")
#     file_name = models.CharField(max_length=255, default="")
#     audio_file_path = models.CharField(max_length=255, default="")
#     downloaded = models.BooleanField(default=False)
#     transcribed = models.BooleanField(default=False)
#     cleaned = models.BooleanField(default=False)
#     transcript = models.TextField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

# app/models.py
# core/models.py
from django.db import models

class VideoStatus(models.TextChoices):
    NEW = "NEW", "Discovered"
    TRANSFERRING = "TRANSFERRING", "Transferring to GCS"
    TRANSFER_FAILED = "TRANSFER_FAILED", "Transfer failed"
    TRANSFER_DONE = "TRANSFER_DONE", "Transfer complete"
    TRANSCRIBING = "TRANSCRIBING", "Transcribing"
    TRANSCRIBE_FAILED = "TRANSCRIBE_FAILED", "Transcription failed"
    COMPLETE = "COMPLETE", "Complete"

class Video(models.Model):
    title = models.CharField(max_length=500)
    source = models.CharField(max_length=20)  # "house" or "senate"
    source_url = models.URLField(default="")
    player_url = models.URLField(default="")
    published_at = models.DateTimeField()

    bucket = models.CharField(max_length=255, default="mi-vid-transcription")
    gcs_object = models.CharField(max_length=1024, null=True, blank=True)

    sts_job_name = models.CharField(max_length=512, null=True, blank=True)
    vi_operation_name = models.CharField(max_length=512, null=True, blank=True)

    status = models.CharField(
        max_length=32,
        choices=VideoStatus.choices,
        default=VideoStatus.NEW
    )
    error_message = models.TextField(null=True, blank=True)
    transcript_text = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

