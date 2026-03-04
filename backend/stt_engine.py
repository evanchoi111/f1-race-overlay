"""
stt_engine.py
Wraps OpenAI Whisper to transcribe audio chunks into text.
"""

import whisper
import numpy as np
import tempfile
import soundfile as sf

_model = None


def load_model(model_size: str = "base") -> whisper.Whisper:
    """
    Load and cache the Whisper model.
    Call this once at startup before transcribing.

    model_size options:
      - "tiny"   → fastest, least accurate (~1GB RAM)
      - "base"   → good balance, recommended for MVP (~1GB RAM)
      - "small"  → more accurate, slower (~2GB RAM)
      - "medium" → best accuracy, slow on CPU (~5GB RAM)
    """
    global _model
    if _model is None:
        print(f"[STT] Loading Whisper model: {model_size}")
        _model = whisper.load_model(model_size)
        print("[STT] Model loaded and ready.")
    return _model


def transcribe(audio: np.ndarray, sample_rate: int = 16000) -> str:
    """
    Transcribe a numpy audio array and return the transcript as a string.

    Args:
        audio: numpy array of audio samples (float32, mono)
        sample_rate: sample rate of the audio (Whisper expects 16000 Hz)

    Returns:
        Transcribed text string, or empty string if transcription fails.
    """
    global _model
    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    try:
        # Whisper expects float32 audio at 16kHz
        audio = audio.astype(np.float32)

        # Resample if needed
        if sample_rate != 16000:
            import librosa
            audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=16000)

        # Write to a temp .wav file (Whisper works best from file)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, audio, 16000)
            result = _model.transcribe(
                tmp.name,
                language="en",        # F1 commentary is English
                fp16=False,           # fp16=True only if you have a CUDA GPU
                verbose=False,
            )

        transcript = result["text"].strip()
        print(f"[STT] Transcript: {transcript}")
        return transcript

    except Exception as e:
        print(f"[STT] Transcription error: {e}")
        return ""


def transcribe_file(filepath: str) -> str:
    """
    Convenience function to transcribe directly from an audio file path.
    Useful for testing without live audio capture.

    Args:
        filepath: path to any audio file (.wav, .mp3, .m4a, etc.)

    Returns:
        Transcribed text string.
    """
    global _model
    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    print(f"[STT] Transcribing file: {filepath}")
    result = _model.transcribe(filepath, language="en", fp16=False, verbose=False)
    transcript = result["text"].strip()
    print(f"[STT] Transcript: {transcript}")
    return transcript


# --- Quick test ---
# Run this file directly to verify Whisper is working:
# python stt_engine.py
if __name__ == "__main__":
    import sys

    model = load_model("base")

    if len(sys.argv) > 1:
        # Test with a file: python stt_engine.py path/to/audio.wav
        text = transcribe_file(sys.argv[1])
        print(f"\nResult: {text}")
    else:
        # Test with a short silent numpy array (just confirms model loads)
        print("No audio file provided. Testing with silent audio...")
        dummy_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        text = transcribe(dummy_audio)
        print("Model is working. Pass an audio file to test transcription:")
        print("  python stt_engine.py path/to/clip.wav")