"""
stt_engine.py
Wraps a speech-to-text model (default: OpenAI Whisper) and returns
transcribed text from raw audio chunks.
"""

# TODO: pip install openai-whisper
# import whisper

def load_model(model_size="base"):
    """
    Load and return the Whisper model.
    model_size options: tiny, base, small, medium (base recommended for MVP)
    """
    raise NotImplementedError

def transcribe(model, audio_chunk) -> str:
    """
    Transcribe a raw audio chunk and return the text string.
    """
    raise NotImplementedError