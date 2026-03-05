"""
websocket_server.py
Ties everything together: captures audio → transcribes → checks triggers
→ broadcasts popup events to all connected WebSocket clients (Chrome extension).

Run this to start the full backend:
    python websocket_server.py
"""

import asyncio
import json
import threading
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
model = None
loop = None
trigger_queue = None


# ── WebSocket handler ────────────────────────────────────────────────────────

async def handler(websocket):
    """Handle a new Chrome extension client connecting."""
    CONNECTED_CLIENTS.add(websocket)
    client = websocket.remote_address
    print(f"[WS] Client connected: {client} — Total: {len(CONNECTED_CLIENTS)}")
    try:
        await websocket.wait_closed()
    finally:
        CONNECTED_CLIENTS.discard(websocket)
        print(f"[WS] Client disconnected: {client} — Total: {len(CONNECTED_CLIENTS)}")


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


# ── Audio pipeline ───────────────────────────────────────────────────────────

def on_audio_chunk(audio):
    """
    Called from the audio capture thread for each chunk.
    Transcribes and checks for triggers, then queues any event.
    """
    text = transcribe(audio)
    if not text:
        return

    event = process_transcript(text)
    if event:
        # Put the event into the asyncio queue from the background thread
        asyncio.run_coroutine_threadsafe(
            trigger_queue.put(event),
            loop
        )


async def trigger_dispatcher():
    """
    Async loop that reads from the trigger queue and broadcasts to clients.
    """
    while True:
        event = await trigger_queue.get()
        await broadcast(event)


def start_audio_thread(stop_event):
    """Run audio capture in a background thread."""
    start_capture(on_audio_chunk, stop_event=stop_event)


# ── Main ─────────────────────────────────────────────────────────────────────

async def main():
    global model, loop, trigger_queue

    # Create the queue inside the running event loop
    trigger_queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    print("[Server] Loading Whisper model...")
    model = load_model("base")
    print("[Server] Model ready.")

    # Start audio capture in a background thread
    stop_event = threading.Event()
    audio_thread = threading.Thread(
        target=start_audio_thread,
        args=(stop_event,),
        daemon=True,
    )
    audio_thread.start()
    print("[Server] Audio capture started.")

    # Start the trigger dispatcher
    asyncio.create_task(trigger_dispatcher())

    # Start the WebSocket server
    async with websockets.serve(handler, HOST, PORT):
        print(f"[Server] WebSocket server running on ws://{HOST}:{PORT}")
        print("[Server] Waiting for Chrome extension to connect...")
        print("[Server] Press Ctrl+C to stop.\n")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Server] Shutting down.")