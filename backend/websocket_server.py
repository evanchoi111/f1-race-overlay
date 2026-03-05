"""
websocket_server.py
Ties everything together:
- Captures mic audio (fallback) OR receives browser tab audio (default)
- Transcribes -> checks triggers -> broadcasts popup events to Chrome extension

Run this to start the full backend:
    python websocket_server.py
"""

import asyncio
import json
import threading
import base64
import numpy as np
import websockets

from audio_capture import start_capture
from stt_engine import load_model, transcribe
from trigger_engine import process_transcript
from content_templates import get_template

# --- Config ---
HOST = "localhost"
PORT = 8765

# --- State ---
CONNECTED_CLIENTS = set()
BROWSER_CLIENTS = set()   # clients sending audio from tab capture
model = None
loop = None
trigger_queue = None
browser_audio_connected = False


# -- WebSocket handler --------------------------------------------------------

async def handler(websocket):
    global browser_audio_connected

    CONNECTED_CLIENTS.add(websocket)
    client = websocket.remote_address
    print(f"[WS] Client connected: {client} - Total: {len(CONNECTED_CLIENTS)}")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except Exception:
                continue

            # Client identifying itself as a browser audio source
            if data.get("type") == "source" and data.get("value") == "browser":
                BROWSER_CLIENTS.add(websocket)
                browser_audio_connected = True
                print("[WS] Browser audio source connected - mic fallback disabled.")

            # Incoming audio chunk from browser tab capture
            elif data.get("type") == "audio":
                raw = base64.b64decode(data["data"])
                audio = np.frombuffer(raw, dtype=np.float32).copy()
                sample_rate = data.get("sample_rate", 16000)

                # Process in background thread to avoid blocking the event loop
                await loop.run_in_executor(
                    None, process_audio_chunk, audio, sample_rate
                )

            # Incoming popup event (legacy direct connection)
            elif data.get("title"):
                pass  # handled by broadcast

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CONNECTED_CLIENTS.discard(websocket)
        BROWSER_CLIENTS.discard(websocket)
        if not BROWSER_CLIENTS:
            browser_audio_connected = False
            print("[WS] Browser audio source disconnected - mic fallback enabled.")
        print(f"[WS] Client disconnected: {client} - Total: {len(CONNECTED_CLIENTS)}")


def process_audio_chunk(audio: np.ndarray, sample_rate: int = 16000):
    """Process an audio chunk from the browser and fire triggers."""
    text = transcribe(audio, sample_rate)
    if not text:
        return
    event = process_transcript(text)
    if event:
        asyncio.run_coroutine_threadsafe(trigger_queue.put(event), loop)


async def broadcast(event_type: str):
    """Send a popup event to all connected Chrome extension clients."""
    template = get_template(event_type)
    if not template:
        return
    if not CONNECTED_CLIENTS:
        print(f"[WS] Trigger '{event_type}' fired but no clients connected.")
        return

    payload = json.dumps({
        "event": event_type,
        "title": template["title"],
        "definition": template["definition"],
        "why_it_matters": template["why_it_matters"],
    })

    print(f"[WS] Broadcasting: {template['title']}")
    await asyncio.gather(
        *[ws.send(payload) for ws in CONNECTED_CLIENTS],
        return_exceptions=True,
    )


# -- Mic audio pipeline (fallback) -------------------------------------------

def on_mic_chunk(audio):
    """Called from the mic capture thread. Only active if no browser source."""
    if browser_audio_connected:
        return  # browser audio takes priority

    text = transcribe(audio)
    if not text:
        return

    event = process_transcript(text)
    if event:
        asyncio.run_coroutine_threadsafe(trigger_queue.put(event), loop)


async def trigger_dispatcher():
    """Reads from the trigger queue and broadcasts to clients."""
    while True:
        event = await trigger_queue.get()
        await broadcast(event)


def start_mic_thread(stop_event):
    """Run mic capture in a background thread as fallback."""
    start_capture(on_mic_chunk, stop_event=stop_event)


# -- Main --------------------------------------------------------------------

async def main():
    global model, loop, trigger_queue

    trigger_queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    print("[Server] Loading Whisper model...")
    model = load_model("base")
    print("[Server] Model ready.")

    # Start mic capture as fallback in background thread
    stop_event = threading.Event()
    mic_thread = threading.Thread(
        target=start_mic_thread,
        args=(stop_event,),
        daemon=True,
    )
    mic_thread.start()
    print("[Server] Mic capture started (fallback mode).")

    asyncio.create_task(trigger_dispatcher())

    async with websockets.serve(handler, HOST, PORT):
        print(f"[Server] WebSocket server running on ws://{HOST}:{PORT}")
        print("[Server] Waiting for Chrome extension to connect...")
        print("[Server] Press Ctrl+C to stop.\n")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Server] Shutting down.")
