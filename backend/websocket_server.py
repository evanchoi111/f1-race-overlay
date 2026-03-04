"""
websocket_server.py
Ties everything together: captures audio → transcribes → checks triggers
→ broadcasts popup events to all connected WebSocket clients.
"""

import asyncio
import json
# TODO: pip install websockets
# import websockets

from trigger_engine import process_transcript
from content_templates import get_template

CONNECTED_CLIENTS = set()
HOST = "localhost"
PORT = 8765


async def handler(websocket):
    CONNECTED_CLIENTS.add(websocket)
    print(f"Client connected. Total: {len(CONNECTED_CLIENTS)}")
    try:
        await websocket.wait_closed()
    finally:
        CONNECTED_CLIENTS.discard(websocket)
        print(f"Client disconnected. Total: {len(CONNECTED_CLIENTS)}")


async def broadcast(event_type: str):
    template = get_template(event_type)
    if not template or not CONNECTED_CLIENTS:
        return
    payload = json.dumps({"event": event_type, **template})
    await asyncio.gather(*[ws.send(payload) for ws in CONNECTED_CLIENTS])


async def audio_pipeline():
    """
    Main loop: capture audio → STT → trigger check → broadcast.
    Replace the stub below with real audio_capture + stt_engine calls.
    """
    # TODO: wire in audio_capture and stt_engine
    # For now, this is a stub you can test manually
    while True:
        await asyncio.sleep(1)


async def main():
    # TODO: uncomment when websockets is installed
    # async with websockets.serve(handler, HOST, PORT):
    #     print(f"WebSocket server running on ws://{HOST}:{PORT}")
    #     await audio_pipeline()
    pass


if __name__ == "__main__":
    asyncio.run(main())