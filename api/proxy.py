from urllib.request import urlopen, Request
from urllib.parse import parse_qs, urlparse
from urllib.error import URLError
from http.server import BaseHTTPRequestHandler
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.tiktok.com/",
}

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        action = qs.get("action", ["info"])[0]
        video_url = qs.get("url", [""])[0]

        if not video_url:
            self._json({"code": -1, "msg": "Missing url"})
            return

        if action == "download":
            # Stream the video file back as MP4
            filename = qs.get("filename", ["video.mp4"])[0]
            try:
                req = Request(video_url, headers=HEADERS)
                with urlopen(req, timeout=60) as resp:
                    self.send_response(200)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                    length = resp.getheader("Content-Length")
                    if length:
                        self.send_header("Content-Length", length)
                    self._cors()
                    self.end_headers()
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except Exception as e:
                self._json({"code": -1, "msg": str(e)})

        else:
            # Fetch video info from tikwm
            upstream = f"https://www.tikwm.com/api/?url={video_url}&hd=1"
            try:
                req = Request(upstream, headers=HEADERS)
                with urlopen(req, timeout=15) as resp:
                    body = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._cors()
                self.end_headers()
                self.wfile.write(body)
            except URLError as e:
                self._json({"code": -1, "msg": f"上游请求失败: {e}"})
            except Exception as e:
                self._json({"code": -1, "msg": str(e)})

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def _json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(500)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(body)
