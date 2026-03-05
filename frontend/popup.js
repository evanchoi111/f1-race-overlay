const MODE_TAB = "tab";
const MODE_MIC = "mic";

const statusEl = document.getElementById("status");
const radioButtons = Array.from(document.querySelectorAll('input[name="audio-mode"]'));

function setStatus(text) {
  statusEl.classList.remove("ok", "error");
  statusEl.textContent = text;
}

function setStatusOk(text) {
  statusEl.classList.remove("error");
  statusEl.classList.add("ok");
  statusEl.textContent = text;
}

function setStatusError(text) {
  statusEl.classList.remove("ok");
  statusEl.classList.add("error");
  statusEl.textContent = text;
}

function setSelectedMode(mode) {
  radioButtons.forEach((radio) => {
    radio.checked = radio.value === mode;
  });
}

function sendMessage(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, (response) => {
      const err = chrome.runtime.lastError;
      if (err) {
        reject(new Error(err.message));
        return;
      }
      resolve(response || { ok: false });
    });
  });
}

async function loadMode() {
  try {
    const response = await sendMessage({ type: "get_audio_mode" });
    if (!response?.ok) {
      throw new Error(response?.error || "Failed to load mode");
    }

    const mode = response.mode === MODE_MIC ? MODE_MIC : MODE_TAB;
    setSelectedMode(mode);
    setStatusOk(mode === MODE_TAB ? "Using tab audio capture" : "Using mic fallback");

    // Ensure tab capture starts without requiring mode flip when tab mode is already selected.
    if (mode === MODE_TAB) {
      const startResponse = await sendMessage({ type: "start_capture_active_tab" });
      if (!startResponse?.ok) {
        throw new Error(startResponse?.error || "Failed to start tab capture");
      }
    }
  } catch (err) {
    setStatusError(`Error: ${err.message}`);
  }
}

async function onModeChange(event) {
  const mode = event.target.value;
  if (mode !== MODE_TAB && mode !== MODE_MIC) return;

  setStatus("Saving...");
  try {
    const response = await sendMessage({ type: "set_audio_mode", mode });
    if (!response?.ok) {
      throw new Error(response?.error || "Failed to save mode");
    }
    setStatusOk(mode === MODE_TAB ? "Using tab audio capture" : "Using mic fallback");
  } catch (err) {
    setStatusError(`Error: ${err.message}`);
  }
}

radioButtons.forEach((radio) => {
  radio.addEventListener("change", onModeChange);
});

loadMode();
