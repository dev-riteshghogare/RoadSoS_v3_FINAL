"""
Voice SOS Module
Uses browser Web Speech API via Streamlit HTML component.
Detects crash keywords, triggers emergency protocol.
"""

VOICE_SOS_HTML = """
<div id="voice-sos-container" style="
    background: linear-gradient(135deg, #0f0c29, #302b63);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    color: white;
    font-family: 'DM Sans', sans-serif;
    border: 2px solid rgba(231,76,60,0.3);
">
    <div id="mic-icon" style="font-size: 3rem; margin-bottom: 0.5rem; cursor: pointer;" onclick="toggleListening()">🎤</div>
    <h3 style="margin: 0 0 0.3rem 0; font-size: 1.1rem;">Voice SOS Mode</h3>
    <p id="status-text" style="margin: 0 0 1rem 0; opacity: 0.7; font-size: 0.85rem;">Click mic or press SPACE to speak</p>

    <button id="voice-btn" onclick="toggleListening()" style="
        background: linear-gradient(135deg, #c0392b, #e74c3c);
        color: white; border: none; border-radius: 50px;
        padding: 0.7rem 2rem; font-size: 1rem; font-weight: 700;
        cursor: pointer; width: 100%; margin-bottom: 0.8rem;
        box-shadow: 0 4px 20px rgba(231,76,60,0.4);
        transition: all 0.2s;
    ">🎤 START LISTENING</button>

    <div id="transcript-box" style="
        background: rgba(255,255,255,0.05);
        border-radius: 10px; padding: 0.8rem;
        min-height: 50px; font-size: 0.9rem;
        border: 1px solid rgba(255,255,255,0.1);
        text-align: left; display: none;
    ">
        <span style="opacity:0.5; font-size:0.8rem;">Transcript:</span>
        <div id="transcript-text" style="margin-top: 0.3rem; color: #fff;"></div>
    </div>

    <div id="crash-alert" style="display:none; margin-top:0.8rem;
        background: linear-gradient(135deg, #c0392b, #922b21);
        border-radius: 10px; padding: 0.8rem;
        animation: flash-alert 0.8s ease-in-out 5;
    ">
        🚨 <strong>CRASH DETECTED!</strong> Emergency protocol activated!
    </div>

    <div id="listening-indicator" style="display:none; margin-top:0.5rem;">
        <div style="display:flex; justify-content:center; gap:4px; align-items:center;">
            <div class="bar"></div><div class="bar"></div><div class="bar"></div>
            <div class="bar"></div><div class="bar"></div>
        </div>
    </div>
</div>

<style>
@keyframes flash-alert { 0%,100%{opacity:1} 50%{opacity:0.6} }
.bar {
    width: 4px; height: 20px; background: #e74c3c;
    border-radius: 2px;
    animation: sound-wave 0.8s ease-in-out infinite alternate;
}
.bar:nth-child(1){animation-delay:0s; height:10px}
.bar:nth-child(2){animation-delay:0.1s; height:20px}
.bar:nth-child(3){animation-delay:0.2s; height:30px}
.bar:nth-child(4){animation-delay:0.3s; height:20px}
.bar:nth-child(5){animation-delay:0.4s; height:10px}
@keyframes sound-wave { from{transform:scaleY(0.5)} to{transform:scaleY(1.5)} }
</style>

<script>
const CRASH_KEYWORDS = [
    'accident','crash','collision','help','emergency','sos','bleeding',
    'unconscious','injured','hurt','fire','trapped','dying','ambulance',
    'police','hospital','pain','broken','fallen'
];

let recognition = null;
let isListening = false;

function initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        document.getElementById('status-text').textContent = '⚠️ Voice not supported in this browser. Use Chrome.';
        return null;
    }
    const r = new SpeechRecognition();
    r.continuous = true;
    r.interimResults = true;
    r.lang = 'en-IN';

    r.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        const box = document.getElementById('transcript-box');
        const text = document.getElementById('transcript-text');
        box.style.display = 'block';
        text.textContent = transcript;

        // Check for crash keywords
        const lower = transcript.toLowerCase();
        const detected = CRASH_KEYWORDS.filter(kw => lower.includes(kw));
        if (detected.length > 0) {
            triggerCrashAlert(transcript, detected);
        }
    };

    r.onerror = (e) => {
        document.getElementById('status-text').textContent = '⚠️ Mic error: ' + e.error + '. Try again.';
        stopListening();
    };

    r.onend = () => { if (isListening) r.start(); };
    return r;
}

function toggleListening() {
    if (isListening) { stopListening(); } else { startListening(); }
}

function startListening() {
    if (!recognition) recognition = initRecognition();
    if (!recognition) return;
    recognition.start();
    isListening = true;
    document.getElementById('voice-btn').textContent = '⏹️ STOP LISTENING';
    document.getElementById('voice-btn').style.background = 'linear-gradient(135deg, #27ae60, #2ecc71)';
    document.getElementById('status-text').textContent = '🔴 Listening... Speak your emergency!';
    document.getElementById('listening-indicator').style.display = 'block';
    document.getElementById('mic-icon').textContent = '🔴';
}

function stopListening() {
    if (recognition) recognition.stop();
    isListening = false;
    document.getElementById('voice-btn').textContent = '🎤 START LISTENING';
    document.getElementById('voice-btn').style.background = 'linear-gradient(135deg, #c0392b, #e74c3c)';
    document.getElementById('status-text').textContent = 'Click mic or press SPACE to speak';
    document.getElementById('listening-indicator').style.display = 'none';
    document.getElementById('mic-icon').textContent = '🎤';
}

function triggerCrashAlert(transcript, keywords) {
    document.getElementById('crash-alert').style.display = 'block';
    document.getElementById('status-text').textContent = '🚨 Emergency detected: ' + keywords.join(', ');
    // Send transcript to Streamlit
    window.parent.postMessage({
        type: 'CRASH_DETECTED',
        transcript: transcript,
        keywords: keywords
    }, '*');
    // Also set value in hidden input for Streamlit to read
    const input = document.getElementById('voice-transcript-output');
    if (input) {
        input.value = transcript;
        input.dispatchEvent(new Event('change'));
    }
}

// SPACE bar shortcut
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
        e.preventDefault();
        toggleListening();
    }
});
</script>
<input type="hidden" id="voice-transcript-output" value="">
"""


def get_voice_component_html(height=320):
    return VOICE_SOS_HTML
