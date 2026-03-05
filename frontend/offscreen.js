/**
 * offscreen.js
 * Runs in an offscreen document to:
 * - capture tab audio via stream id
 * - keep local playback active
 * - resample/send audio to backend WebSocket
 */

const WS_URL = "ws://localhost:8765";
const SAMPLE_RATE = 16000;
const CHUNK_DURATION_MS = 5000;

let socket = null;
let reconnectTimer = null;
let shouldReconnect = false;

let currentTabId = null;
let stream = null;
let audioContext = null;
let processor = null;
let sourceNode = null;
let passthroughNode = null;
let capturing = false;
let sampleBuffer = [];

function notifyError(error) {
  chrome.runtime.sendMessage({
    type: "capture_error",
    error: String(error),
  });
}

function clearReconnectTimer() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
}

function float32ToBase64(float32Array) {
  const bytes = new Uint8Array(float32Array.buffer);
  const chunkSize = 0x8000;
  let binary = "";

  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }

  return btoa(binary);
}

function connectWebSocket() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  socket = new WebSocket(WS_URL);

  socket.onopen = () => {
    socket.send(JSON.stringify({ type: "source", value: "browser" }));
  };

  socket.onclose = () => {
    socket = null;
    if (shouldReconnect) {
      reconnectTimer = setTimeout(connectWebSocket, 3000);
    }
  };

  socket.onerror = () => {
    // onclose handles retry
  };
}

function closeWebSocket() {
  shouldReconnect = false;
  clearReconnectTimer();

  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    socket.close();
  }
  socket = null;
}

function sendChunk(chunk) {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    return;
  }

  socket.send(
    JSON.stringify({
      type: "audio",
      data: float32ToBase64(chunk),
      sample_rate: SAMPLE_RATE,
    })
  );
}

async function stopCapture() {
  if (processor) {
    processor.disconnect();
    processor.onaudioprocess = null;
    processor = null;
  }

  if (sourceNode) {
    sourceNode.disconnect();
    sourceNode = null;
  }

  if (passthroughNode) {
    passthroughNode.disconnect();
    passthroughNode = null;
  }

  if (audioContext) {
    await audioContext.close();
    audioContext = null;
  }

  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    stream = null;
  }

  closeWebSocket();

  sampleBuffer = [];
  currentTabId = null;
  capturing = false;
}

async function startCapture(tabId, streamId) {
  if (!streamId) {
    throw new Error("Missing streamId");
  }

  if (capturing) {
    if (currentTabId === tabId) return;
    await stopCapture();
  }

  shouldReconnect = true;
  connectWebSocket();

  stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      mandatory: {
        chromeMediaSource: "tab",
        chromeMediaSourceId: streamId,
      },
    },
    video: false,
  });

  audioContext = new AudioContext({ sampleRate: SAMPLE_RATE });
  sourceNode = audioContext.createMediaStreamSource(stream);
  processor = audioContext.createScriptProcessor(4096, 1, 1);
  passthroughNode = audioContext.createGain();

  const samplesPerChunk = SAMPLE_RATE * (CHUNK_DURATION_MS / 1000);

  processor.onaudioprocess = (event) => {
    const inputData = event.inputBuffer.getChannelData(0);
    sampleBuffer.push(...inputData);

    while (sampleBuffer.length >= samplesPerChunk) {
      const chunk = new Float32Array(sampleBuffer.splice(0, samplesPerChunk));
      sendChunk(chunk);
    }
  };

  // Keep tab audio audible for users with headphones.
  sourceNode.connect(passthroughNode);
  passthroughNode.connect(audioContext.destination);

  // Also feed STT pipeline.
  sourceNode.connect(processor);
  processor.connect(audioContext.destination);

  capturing = true;
  currentTabId = tabId;
}

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === "offscreen_start_capture") {
    startCapture(message.tabId, message.streamId).catch(notifyError);
    return;
  }

  if (message.type === "offscreen_stop_capture") {
    stopCapture().catch(notifyError);
  }
});
