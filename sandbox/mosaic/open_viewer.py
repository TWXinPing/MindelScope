"""Open the MOSAIC sandbox viewer in a browser (no extra dependencies)."""

from __future__ import annotations

import http.server
import socketserver
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PORT = 8765
URL = f"http://127.0.0.1:{PORT}/sandbox/mosaic/viewer/"


def main() -> None:
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)

    def serve() -> None:
        httpd.serve_forever()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    print(f"Opening {URL}")
    print("Press Ctrl+C to stop.")
    webbrowser.open(URL)
    try:
        thread.join()
    except KeyboardInterrupt:
        httpd.shutdown()


if __name__ == "__main__":
    import os

    os.chdir(ROOT)
    main()
