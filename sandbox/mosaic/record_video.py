"""Record the MOSAIC viewer tour to an MP4 you can send to collaborators."""

from __future__ import annotations

import http.server
import os
import shutil
import socketserver
import subprocess
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent / "share"
PORT = 8766
URL = "http://127.0.0.1:%s/sandbox/mosaic/viewer/index.html?tour=1" % PORT
MP4 = OUT_DIR / "MOSAIC-information-flow.mp4"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(str(ROOT))
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), http.server.SimpleHTTPRequestHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    video_dir = OUT_DIR / "_raw"
    if video_dir.exists():
        shutil.rmtree(str(video_dir))
    video_dir.mkdir()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=str(video_dir),
            record_video_size={"width": 1440, "height": 900},
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_selector("body[data-tour='done']", timeout=120000)
        page.wait_for_timeout(800)
        page.close()
        raw = Path(page.video.path())
        context.close()
        browser.close()

    httpd.shutdown()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(raw),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(MP4),
    ]
    subprocess.check_call(cmd)
    shutil.rmtree(str(video_dir))
    print("Wrote %s (%.1f MB)" % (MP4, MP4.stat().st_size / 1e6))


if __name__ == "__main__":
    main()
