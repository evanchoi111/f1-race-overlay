/**
 * content.js
 * Injected into pages to request capture and render popup events.
 */

const WS_URL = "ws://localhost:8765";
let socket = null;
let captureRequested = false;

function requestCapture() {
  if (captureRequested) return;
  captureRequested = true;
  chrome.runtime.sendMessage({ type: "start_capture" });
}

function requestCaptureIfVisibleTopFrame() {
  if (window.top !== window) return;
  if (document.visibilityState !== "visible") return;
  requestCapture();
}

function connectPopupWebSocket() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  socket = new WebSocket(WS_URL);

  socket.onmessage = (msg) => {
    try {
      const data = JSON.parse(msg.data);
      if (data.title) {
        showPopup(data);
      }
    } catch {
      // Ignore malformed payloads
    }
  };

  socket.onclose = () => {
    socket = null;
    setTimeout(connectPopupWebSocket, 3000);
  };
}

function showPopup({ title, definition, why_it_matters }) {
  document.getElementById("f1-overlay-popup")?.remove();

  const popup = document.createElement("div");
  popup.id = "f1-overlay-popup";
  popup.innerHTML = `
    <div class="f1-overlay-header">${title}</div>
    <div class="f1-overlay-body">
      <p>${definition}</p>
      <p class="f1-overlay-why"><strong>Why it matters:</strong> ${why_it_matters}</p>
    </div>
    <button class="f1-overlay-close" onclick="this.parentElement.remove()">✕</button>
  `;
  document.body.appendChild(popup);

  setTimeout(() => popup.remove(), 20000);
}

document.addEventListener("visibilitychange", () => {
  requestCaptureIfVisibleTopFrame();
});

connectPopupWebSocket();
requestCaptureIfVisibleTopFrame();
