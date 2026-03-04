# f1-race-overlay

# 🏎️ F1 Race Overlay

A real-time educational overlay for Formula 1 viewers. When something happens on track — a yellow flag, red flag, safety car, pit stop, or penalty — a popup appears in your browser explaining what it is and why it matters.

Built for new F1 fans who want to understand what's going on without having to pause and Google everything.

---

## How It Works

1. A local Python backend listens to your system audio using your microphone
2. [OpenAI Whisper](https://github.com/openai/whisper) transcribes the F1 commentary in real time
3. A trigger engine scans the transcript for key phrases ("yellow flag", "safety car deployed", "red flag", etc.)
4. When a trigger fires, the backend broadcasts the event over a WebSocket
5. A Chrome extension receives the event and displays a popup on top of whatever you're watching

```
Live F1 commentary
       ↓
  Whisper STT
       ↓
  Trigger engine
       ↓
 WebSocket server
       ↓
 Chrome extension → popup appears in browser
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Speech-to-text | OpenAI Whisper (base model, runs locally) |
| Audio capture | sounddevice + numpy |
| Backend | Python, asyncio, websockets |
| Frontend | Chrome Extension (Manifest V3), vanilla JS |

---

## Getting Started

### Prerequisites
- Python 3.9+
- Google Chrome
- [ffmpeg](https://ffmpeg.org/) — required by Whisper for audio processing

Install ffmpeg on macOS:
```bash
brew install ffmpeg
```

### Installation

1. Clone the repo:
```bash
git clone https://github.com/evanchoi111/f1-race-overlay.git
cd f1-race-overlay
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the Backend

```bash
cd backend
python websocket_server.py
```

The first run will download the Whisper base model (~140MB). After that it starts instantly.

### Loading the Chrome Extension

1. Open Chrome and go to `chrome://extensions`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked**
4. Select the `frontend/` folder from this repo

Once loaded, the extension will automatically connect to the backend WebSocket server whenever it's running.

### Usage

1. Start the backend with `python websocket_server.py`
2. Open any F1 stream in Chrome (F1 TV, YouTube, etc.)
3. Play audio through your speakers — the backend listens via mic
4. When a flag or event is detected, a popup appears automatically

---

## Supported Events

| Event | Trigger Phrases |
|---|---|
| 🟡 Yellow Flag | "yellow flag", "double yellow" |
| 🔴 Red Flag | "red flag" |
| 🚗 Safety Car | "safety car", "safety car deployed" |
| VSC | "virtual safety car" |
| 🔧 Pit Stop | "pit stop", "into the pits" |
| ⚠️ Penalty | "penalty", "drive-through", "five-second penalty" |
| 🔍 Investigation | "investigation" |

---

## Roadmap

- [ ] System audio capture (so it works with headphones, no mic needed)
- [ ] Beginner / minimal mode toggle in the extension
- [ ] Support for more events (DRS enabled, fastest lap, etc.)
- [ ] Smarter NLP-based trigger detection
- [ ] On-screen popup positioning options

---

## License

MIT
