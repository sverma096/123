let recognition;

function startRecognition() {
    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();

    recognition.lang = "hi-IN";
    recognition.continuous = true;

    recognition.onresult = function(event) {
        let text = "";

        for (let i = 0; i < event.results.length; i++) {
            text += event.results[i][0].transcript;
        }

        document.getElementById("textInput").value = text;
    };

    recognition.start();
}

function stopRecognition() {
    if (recognition) recognition.stop();
}
