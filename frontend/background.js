/**
 * background.js
 * Service worker that coordinates tab capture via an offscreen document
 * and forwards popup payloads to content scripts.
 */

const OFFSCREEN_PATH = "offscreen.html";
const OFFSCREEN_URL = chrome.runtime.getURL(OFFSCREEN_PATH);
let creatingOffscreen = null;

async function hasOffscreenDocument() {
  if (!chrome.runtime.getContexts) {
    return false;
  }

  const contexts = await chrome.runtime.getContexts({
    contextTypes: ["OFFSCREEN_DOCUMENT"],
    documentUrls: [OFFSCREEN_URL],
  });

  return contexts.length > 0;
}

async function ensureOffscreenDocument() {
  const exists = await hasOffscreenDocument();
  if (exists) return;

  if (!creatingOffscreen) {
    creatingOffscreen = chrome.offscreen.createDocument({
      url: OFFSCREEN_PATH,
      reasons: ["USER_MEDIA"],
      justification: "Capture tab audio for speech-to-text while preserving local playback.",
    }).catch((err) => {
      if (!String(err).includes("Only a single offscreen document")) {
        throw err;
      }
    }).finally(() => {
      creatingOffscreen = null;
    });
  }

  await creatingOffscreen;
}

async function getStreamId(tabId) {
  return new Promise((resolve, reject) => {
    chrome.tabCapture.getMediaStreamId({ targetTabId: tabId }, (id) => {
      const err = chrome.runtime.lastError;
      if (err || !id) {
        reject(new Error(err?.message || "Failed to get tab stream id"));
        return;
      }
      resolve(id);
    });
  });
}

async function startCaptureForTab(tabId) {
  if (!tabId) {
    console.warn("[F1 Overlay] No tabId supplied for start_capture.");
    return;
  }

  try {
    await ensureOffscreenDocument();
    const streamId = await getStreamId(tabId);

    chrome.runtime.sendMessage({
      type: "offscreen_start_capture",
      tabId,
      streamId,
    });
  } catch (err) {
    console.error("[F1 Overlay] Failed to start capture:", err);
  }
}

async function stopCapture() {
  try {
    await ensureOffscreenDocument();
    chrome.runtime.sendMessage({ type: "offscreen_stop_capture" });
  } catch (err) {
    console.error("[F1 Overlay] Failed to stop capture:", err);
  }
}

function broadcastPopup(data) {
  chrome.tabs.query({}, (tabs) => {
    tabs.forEach((tab) => {
      chrome.tabs.sendMessage(tab.id, { type: "popup", data }).catch(() => {});
    });
  });
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "start_capture") {
    startCaptureForTab(sender.tab?.id);
    sendResponse?.({ ok: true });
    return true;
  }

  if (message.type === "stop_capture") {
    stopCapture();
    sendResponse?.({ ok: true });
    return true;
  }

  if (message.type === "popup") {
    broadcastPopup(message.data);
    return;
  }

  if (message.type === "capture_error") {
    console.error("[F1 Overlay] Capture error:", message.error);
  }
});

chrome.action.onClicked.addListener((tab) => {
  if (tab?.id) {
    startCaptureForTab(tab.id);
  }
});
