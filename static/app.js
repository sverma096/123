
let recognition = null;
let isListening = false;

const statusText = () => document.getElementById("statusText");
const textArea = () => document.getElementById("text");

function setStatus(message) {
  statusText().textContent = message;
}

function buildPreviewHtml(rawText) {
  const lines = rawText.split("\n");
  let html = "";
  let titleDone = false;
  for (const line of lines) {
    const safe = line
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    if (!titleDone && safe.trim()) {
      html += `<div class="preview-title">${safe}</div>`;
      titleDone = true;
    } else if (!safe.trim()) {
      html += `<div style="height:10px"></div>`;
    } else {
      html += `<div>${safe}</div>`;
    }
  }
  return `<div class="preview-content">${html}</div>`;
}

async function generatePreview() {
  const payload = {
    title: document.getElementById("title").value,
    text: document.getElementById("text").value,
    ai_enabled: document.getElementById("ai_enabled").checked,
    signature: document.getElementById("signature").checked,
    stamp: document.getElementById("stamp").checked
  };

  const box = document.getElementById("previewBox");
  box.innerHTML = `<div class="preview-placeholder"><div><div class="preview-icon">⏳</div><h4>Generating preview</h4><p>Please wait a moment...</p></div></div>`;

  try {
    const res = await fetch("/preview", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    box.innerHTML = buildPreviewHtml(data.preview || "");
  } catch (e) {
    box.innerHTML = `<div class="preview-placeholder"><div><div class="preview-icon">⚠️</div><h4>Preview failed</h4><p>Please try again.</p></div></div>`;
  }
}

function startRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
    return;
  }

  if (!recognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
      isListening = true;
      setStatus("Listening");
    };

    recognition.onend = () => {
      isListening = false;
      setStatus("Ready");
    };

    recognition.onerror = (event) => {
      setStatus("Error: " + event.error);
    };

    recognition.onresult = (event) => {
      let finalTranscript = "";
      let interimTranscript = "";
      for (let i = 0; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + " ";
        } else {
          interimTranscript += transcript;
        }
      }
      const existing = textArea().dataset.finalText || "";
      const updated = (existing + finalTranscript).trim();
      textArea().dataset.finalText = updated ? updated + " " : "";
      textArea().value = (updated + " " + interimTranscript).trim();
    };
  }

  recognition.lang = document.getElementById("languageMode").value;
  try {
    recognition.start();
  } catch (e) {
    // ignore repeated start
  }
}

function stopRecognition() {
  if (recognition && isListening) {
    recognition.stop();
  }
}

function clearEditor() {
  textArea().value = "";
  textArea().dataset.finalText = "";
}

function loadSample() {
  const sample = `This deed is made on this 10th day of April 2026 between the parties.
new paragraph
The first party agrees to provide consulting services in accordance with mutually agreed scope and timelines full stop
new paragraph
Payment shall be released within thirty days from the date of invoice comma subject to satisfactory completion of services full stop`;
  textArea().value = sample;
  textArea().dataset.finalText = sample + " ";
}

document.getElementById("startBtn").addEventListener("click", startRecognition);
document.getElementById("stopBtn").addEventListener("click", stopRecognition);
document.getElementById("clearBtn").addEventListener("click", clearEditor);
document.getElementById("sampleBtn").addEventListener("click", loadSample);
document.getElementById("previewBtn").addEventListener("click", generatePreview);
document.getElementById("previewBtnTop").addEventListener("click", generatePreview);

document.getElementById("languageMode").addEventListener("change", () => {
  if (recognition && isListening) {
    recognition.stop();
  }
  setStatus("Ready");
});
