/**
 * content.js
 * Connects to the local WebSocket server and renders event popups
 * on top of the streaming page.
 */

const WS_URL = "ws://localhost:8765";
let socket;

function connect() {
  socket = new WebSocket(WS_URL);

  socket.onopen = () => console.log("[F1 Overlay] Connected to backend.");
  socket.onmessage = (msg) => {
    const data = JSON.parse(msg.data);
    showPopup(data);
  };
  socket.onclose = () => {
    console.log("[F1 Overlay] Disconnected. Retrying in 5s...");
    setTimeout(connect, 5000);
  };
}

function showPopup({ title, definition, why_it_matters }) {
  // Remove any existing popup
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

  // Auto-dismiss after 20 seconds
  setTimeout(() => popup.remove(), 20000);
}

connect();