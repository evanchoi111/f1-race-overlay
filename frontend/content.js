/**
 * content.js
 * Injected into pages to request tab capture and render popup events.
 */

let captureStarted = false;

function requestCapture() {
  if (captureStarted) return;
  captureStarted = true;
  chrome.runtime.sendMessage({ type: "start_capture" });
}

function requestCaptureIfVisibleTopFrame() {
  if (window.top !== window) return;
  if (document.visibilityState !== "visible") return;
  requestCapture();
}

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === "popup") {
    showPopup(message.data);
  }
});

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

requestCaptureIfVisibleTopFrame();
