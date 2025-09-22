from faster_whisper import WhisperModel

_model = None

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