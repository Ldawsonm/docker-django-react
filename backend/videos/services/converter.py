from moviepy import VideoFileClip

def video_to_audio(video_file_path: str) -> str:
    video_file_clip = VideoFileClip(video_file_path)
    audio = video_file_clip.audio
    return audio