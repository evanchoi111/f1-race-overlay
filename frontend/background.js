/**
 * background.js
 * Service worker that coordinates capture mode and tab audio capture
 * via an offscreen document.
 */

const OFFSCREEN_PATH = "offscreen.html";
const OFFSCREEN_URL = chrome.runtime.getURL(OFFSCREEN_PATH);
const AUDIO_MODE_KEY = "audioMode";
const AUDIO_MODE_TAB = "tab";
const AUDIO_MODE_MIC = "mic";

let creatingOffscreen = null;
let activeCaptureTabId = null;

async function hasOffscreenDocument() {
  if (!chrome.runtime.getContexts) return false;

  const contexts = await chrome.runtime.getContexts({
    contextTypes: ["OFFSCREEN_DOCUMENT"],
    documentUrls: [OFFSCREEN_URL],
  });
  return contexts.length > 0;
}

async function ensureOffscreenDocument() {
  if (await hasOffscreenDocument()) return;

  if (!creatingOffscreen) {
    creatingOffscreen = chrome.offscreen
      .createDocument({
        url: OFFSCREEN_PATH,
        reasons: ["USER_MEDIA"],
        justification: "Capture tab audio for speech-to-text while preserving local playback.",
      })
      .catch((err) => {
        if (!String(err).includes("Only a single offscreen document")) throw err;
      })
      .finally(() => {
        creatingOffscreen = null;
      });
  }

  await creatingOffscreen;
}

async function getAudioMode() {
  const result = await chrome.storage.local.get(AUDIO_MODE_KEY);
  return result[AUDIO_MODE_KEY] || AUDIO_MODE_TAB;
}

async function setAudioMode(mode) {
  if (mode !== AUDIO_MODE_TAB && mode !== AUDIO_MODE_MIC) return;

  await chrome.storage.local.set({ [AUDIO_MODE_KEY]: mode });

  if (mode === AUDIO_MODE_MIC) {
    await stopCapture();
    return;
  }

  const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  if (tab?.id) {
    await startCaptureForTab(tab.id);
  }
}

async function startCaptureForActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  if (!tab?.id) return;
  await startCaptureForTab(tab.id);
}

async function maybeStartCaptureForActiveTab() {
  const mode = await getAudioMode();
  if (mode !== AUDIO_MODE_TAB) return;
  await startCaptureForActiveTab();
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

  if (activeCaptureTabId === tabId) {
    return;
  }

  try {
    if (activeCaptureTabId && activeCaptureTabId !== tabId) {
      await stopCapture();
    }

    await ensureOffscreenDocument();
    const streamId = await getStreamId(tabId);

    chrome.runtime.sendMessage({
      type: "offscreen_start_capture",
      tabId,
      streamId,
    });

    activeCaptureTabId = tabId;
  } catch (err) {
    console.error("[F1 Overlay] Failed to start capture:", err);
  }
}

async function maybeStartCaptureForTab(tabId) {
  const mode = await getAudioMode();
  if (mode !== AUDIO_MODE_TAB) return;
  await startCaptureForTab(tabId);
}

async function stopCapture() {
  try {
    await ensureOffscreenDocument();
    chrome.runtime.sendMessage({ type: "offscreen_stop_capture" });
  } catch (err) {
    console.error("[F1 Overlay] Failed to stop capture:", err);
  } finally {
    activeCaptureTabId = null;
  }
}

chrome.runtime.onInstalled.addListener(async () => {
  const result = await chrome.storage.local.get(AUDIO_MODE_KEY);
  if (!result[AUDIO_MODE_KEY]) {
    await chrome.storage.local.set({ [AUDIO_MODE_KEY]: AUDIO_MODE_TAB });
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "start_capture") {
    maybeStartCaptureForTab(sender.tab?.id)
      .then(() => sendResponse?.({ ok: true }))
      .catch((err) => sendResponse?.({ ok: false, error: String(err) }));
    return true;
  }

  if (message.type === "stop_capture") {
    stopCapture()
      .then(() => sendResponse?.({ ok: true }))
      .catch((err) => sendResponse?.({ ok: false, error: String(err) }));
    return true;
  }

  if (message.type === "set_audio_mode") {
    setAudioMode(message.mode)
      .then(() => sendResponse?.({ ok: true }))
      .catch((err) => sendResponse?.({ ok: false, error: String(err) }));
    return true;
  }

  if (message.type === "get_audio_mode") {
    getAudioMode()
      .then((mode) => sendResponse?.({ ok: true, mode }))
      .catch((err) => sendResponse?.({ ok: false, error: String(err) }));
    return true;
  }

  if (message.type === "start_capture_active_tab") {
    maybeStartCaptureForActiveTab()
      .then(() => sendResponse?.({ ok: true }))
      .catch((err) => sendResponse?.({ ok: false, error: String(err) }));
    return true;
  }

  if (message.type === "capture_error") {
    console.error("[F1 Overlay] Capture error:", message.error);
  }
});
