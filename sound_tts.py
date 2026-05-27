"""
sound_tts.py — Sons WAV + TTS Web Speech API
Sons chargés depuis assets/ encodés base64, joués via <audio> HTML.
TTS via Web Speech API native du navigateur (français).
"""

import streamlit.components.v1 as components
import base64, os

_HERE = os.path.dirname(os.path.abspath(__file__))

def _b64(filename: str) -> str:
    path = os.path.join(_HERE, "assets", filename)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Cache base64 au démarrage
try:
    _SND_ERROR = _b64("sound_error.wav")
    _SND_GOOD  = _b64("sound_good.wav")
except Exception:
    _SND_ERROR = _SND_GOOD = ""


def _play_b64(b64_data: str, volume: float = 1.0):
    if not b64_data:
        return
    html = f"""
    <script>
    (function(){{
        try {{
            const audio = new Audio('data:audio/wav;base64,{b64_data}');
            audio.volume = {volume};
            audio.play().catch(()=>{{}});
        }} catch(e) {{}}
    }})();
    </script>
    """
    components.html(html, height=0, scrolling=False)


def play_error():
    """Son grave descendant pour faux mouvement."""
    _play_b64(_SND_ERROR, volume=0.85)


def play_good():
    """Ding lumineux pour bon mouvement / répétition validée."""
    _play_b64(_SND_GOOD, volume=0.9)


def speak(text: str, lang: str = "fr-FR", rate: float = 1.0):
    """Lit une phrase via Web Speech API (voix française native du browser)."""
    text_safe = text.replace("'", " ").replace('"', ' ').replace("\n", " ")[:200]
    html = f"""
    <script>
    (function(){{
        try {{
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance('{text_safe}');
            u.lang  = '{lang}';
            u.rate  = {rate};
            u.pitch = 1.0;
            function doSpeak() {{
                const voices = window.speechSynthesis.getVoices();
                const fr = voices.find(v => v.lang && v.lang.startsWith('fr'));
                if (fr) u.voice = fr;
                window.speechSynthesis.speak(u);
            }}
            if (window.speechSynthesis.getVoices().length > 0) {{
                doSpeak();
            }} else {{
                window.speechSynthesis.onvoiceschanged = doSpeak;
            }}
        }} catch(e) {{}}
    }})();
    </script>
    """
    components.html(html, height=0, scrolling=False)