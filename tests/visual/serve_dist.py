"""Serve site/dist under /olist-analytics/ with clean URLs, the way GitHub Pages does.

Usage: python tests/visual/serve_dist.py [port]
"""

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DIST = Path(__file__).resolve().parents[2] / "site" / "dist"
BASE = "/olist-analytics"


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        path = path.split("?", 1)[0].split("#", 1)[0]
        if not path.startswith(BASE):
            return str(DIST / "__missing__")
        rel = path[len(BASE) :].lstrip("/") or "index.html"
        target = DIST / rel
        if not target.exists() and (DIST / f"{rel}.html").exists():
            target = DIST / f"{rel}.html"
        return str(target)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4173
    ThreadingHTTPServer(("127.0.0.1", port), partial(Handler)).serve_forever()
