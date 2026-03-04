"""
audio_capture.py
Captures system audio or microphone input and yields raw audio chunks
for the STT engine to process.
"""

# TODO: implement audio capture using sounddevice or pyaudio
# Yields numpy audio arrays at a configurable sample rate

def start_capture(callback, sample_rate=16000, chunk_duration_s=5):
    """
    Start capturing audio and call `callback(audio_chunk)` for each chunk.
    chunk_duration_s: how many seconds of audio per chunk sent to STT
    """
    raise NotImplementedError
