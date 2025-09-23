from faster_whisper import WhisperModel
from google.cloud import videointelligence_v1 as vi
from google.oauth2 import service_account

_model = None
_client = None

def load_model():
    global _model
    if _model is None:
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model

def transcribe_audio(audio_file_path : str) -> str:
    model = load_model()
    segments, _ = model.transcribe(audio_file_path)

    result = ""
    for segment in segments:
        result = result + segment.text

    return result

def init_transcriber_service():
    global _client
    # if _client is None:
    credentials = service_account.Credentials.from_service_account_file(
        "/srv/app/credentials/google-vid-int.json"
        )
    _client = vi.VideoIntelligenceServiceClient(credentials=credentials)
    return _client

def transcribe_video(gcs_uri: str):
    client = init_transcriber_service()

    features = [vi.Feature.SPEECH_TRANSCRIPTION]
    config = vi.SpeechTranscriptionConfig(
        language_code="en-US",
        enable_automatic_punctuation=True,
        enable_speaker_diarization=True,
        diarization_speaker_count=6,  # optional, estimate number of speakers
    )
    video_context = vi.VideoContext(speech_transcription_config=config)

    operation = client.annotate_video(
        request={
            "features": features,
            "input_uri": gcs_uri,
            "video_context": video_context,
        }
    )

    print("Waiting for operation to complete...")
    result = operation.result(timeout=600)  # increase for long videos

    transcriptions = []
    for speech_transcription in result.annotation_results[0].speech_transcriptions:
        for alternative in speech_transcription.alternatives:
            transcriptions.append(alternative.transcript)

    return " ".join(transcriptions)