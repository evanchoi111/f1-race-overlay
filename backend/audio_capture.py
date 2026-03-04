"""
audio_capture.py
Captures system audio or microphone input in real-time and feeds
chunks to the STT engine for transcription.
"""

import sounddevice as sd
import numpy as np
import threading
import queue
import time

# --- Config ---
SAMPLE_RATE = 16000       # Whisper expects 16kHz
CHUNK_DURATION_S = 5      # How many seconds per chunk sent to STT
OVERLAP_DURATION_S = 1    # Overlap between chunks to avoid missing phrases at boundaries
CHANNELS = 1              # Mono audio

CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION_S)
OVERLAP_SAMPLES = int(SAMPLE_RATE * OVERLAP_DURATION_S)


def list_devices():
    """
    Print all available audio input devices.
    Run this to find your system audio / mic device index.
    """
    print("\nAvailable audio devices:")
    print(sd.query_devices())
    print("\nDefault input device:", sd.query_devices(kind='input')['name'])


def start_capture(callback, device=None, stop_event=None):
    """
    Start capturing audio in real-time and call callback(audio_chunk)
    for each chunk of audio.

    Args:
        callback: function that receives a numpy float32 array
        device: audio device index (None = system default mic)
                Run list_devices() to find the right index
        stop_event: threading.Event to stop capture gracefully
    """
    audio_queue = queue.Queue()
    buffer = np.zeros(0, dtype=np.float32)

    if stop_event is None:
        stop_event = threading.Event()

    def audio_callback(indata, frames, time_info, status):
        if status:
            print(f"[Audio] Status: {status}")
        # Flatten to mono and add to queue
        audio_queue.put(indata[:, 0].copy())

    print(f"[Audio] Starting capture — chunk size: {CHUNK_DURATION_S}s, overlap: {OVERLAP_DURATION_S}s")
    print(f"[Audio] Sample rate: {SAMPLE_RATE}Hz, device: {'default' if device is None else device}")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='float32',
        blocksize=1024,
        device=device,
        callback=audio_callback,
    ):
        print("[Audio] Capture started. Press Ctrl+C to stop.")
        while not stop_event.is_set():
            try:
                # Drain the queue into our buffer
                while not audio_queue.empty():
                    chunk = audio_queue.get_nowait()
                    buffer = np.concatenate([buffer, chunk])

                # Once we have enough audio for a full chunk, send it
                if len(buffer) >= CHUNK_SAMPLES:
                    chunk_to_send = buffer[:CHUNK_SAMPLES].copy()
                    # Keep overlap so phrases at chunk boundaries aren't missed
                    buffer = buffer[CHUNK_SAMPLES - OVERLAP_SAMPLES:]
                    callback(chunk_to_send)

                time.sleep(0.1)

            except KeyboardInterrupt:
                break

    print("[Audio] Capture stopped.")


# --- Quick test ---
# Run this file directly to verify your mic is capturing audio:
# python audio_capture.py
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from stt_engine import load_model, transcribe
    from trigger_engine import process_transcript
    from content_templates import get_template

    # List devices first so you can pick the right one if needed
    list_devices()

    model = load_model("base")

    def on_audio_chunk(audio):
        text = transcribe(audio)
        if not text:
            return
        event = process_transcript(text)
        if event:
            template = get_template(event)
            print(f"\n🚨 TRIGGER FIRED: {template['title']}")
            print(f"   {template['definition']}")
            print(f"   Why it matters: {template['why_it_matters']}\n")

    stop = threading.Event()
    try:
        start_capture(on_audio_chunk, stop_event=stop)
    except KeyboardInterrupt:
        stop.set()
        print("\nStopped.")