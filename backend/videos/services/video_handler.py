from moviepy import VideoFileClip
from backend.videos.services.transcriber import transcribe_audio


def handle_transcription(url: str) -> str:
    video_file_path = download_video(url)
    audio_file_path = convert_video_to_audio(video_file_path)
    transcription = transcribe_audio(audio_file_path)
    return transcription

def download_video(url: str) -> str:
    pass

def convert_video_to_audio(video_file_path : str) -> str:
    pass