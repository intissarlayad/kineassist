"""
run.py — Lance KineAssist :
  - index.html   sur http://localhost:8000  (landing page)
  - app.py       sur http://localhost:8501  (Streamlit)

Usage : python run.py
"""
import subprocess
import sys
import os
import threading
import http.server
import socketserver
import webbrowser
import time

PORT_LANDING = 8000
PORT_APP     = 8501
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))


def serve_landing():
    """Sert index.html sur localhost:8000"""
    os.chdir(BASE_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *a: None  # silence logs
    with socketserver.TCPServer(("", PORT_LANDING), handler) as httpd:
        print(f"  Landing page  → http://localhost:{PORT_LANDING}")
        httpd.serve_forever()


def run_streamlit():
    """Lance Streamlit sur localhost:8501"""
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        os.path.join(BASE_DIR, "app.py"),
        "--server.port", str(PORT_APP),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]
    subprocess.run(cmd, cwd=BASE_DIR)


if __name__ == "__main__":
    print("\n🦴 KineAssist — Démarrage...")

    # Landing page dans un thread
    t = threading.Thread(target=serve_landing, daemon=True)
    t.start()

    # Ouvrir le navigateur sur la landing après 1.5s
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{PORT_LANDING}")
    threading.Thread(target=open_browser, daemon=True).start()

    print(f"  App Streamlit → http://localhost:{PORT_APP}")
    print("  Ctrl+C pour arrêter\n")

    # Streamlit en process principal
    run_streamlit()