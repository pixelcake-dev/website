"""The pictures a link to the site shows when it is shared: assets/share-en.png and
assets/share-it.png, 1200 x 630, in the light theme.

tools/share-card.html is the card: this script fills in the words and the drawing
of each language (the one that opens the home page, from tools/drawings.py),
serves the site on a free port of this computer for the time it takes, and has a
Chrome without a window, with a profile of its own, take the picture.

    python tools/share-card.py

Chrome is looked for where Windows installs it; CHROME names another one.
"""

import functools
import http.server
import os
import shutil
import subprocess
import sys
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drawings  # noqa: E402

ROOT = drawings.ROOT
CHROME = os.environ.get("CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")

CARDS = {
    "en": {"line": "The network drawing that <em>answers back.</em>", "strap": "in your browser &middot; no account &middot; open source"},
    "it": {"line": "Il disegno di rete che <em>ti risponde.</em>", "strap": "nel browser &middot; senza account &middot; open source"},
}


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    template = open(os.path.join(ROOT, "tools", "share-card.html"), encoding="utf-8").read()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    profile = tempfile.mkdtemp(prefix="share-card-chrome-")
    try:
        for language, words in CARDS.items():
            page = (
                template.replace("{{lang}}", language)
                .replace("{{line}}", words["line"])
                .replace("{{strap}}", words["strap"])
                .replace("{{drawing}}", drawings.hero(drawings.WORDS[language]["hero"]))
            )
            name = f".share-card-{language}.html"
            path = os.path.join(ROOT, "tools", name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(page)
            target = os.path.join(ROOT, "assets", f"share-{language}.png")
            try:
                subprocess.run(
                    [
                        CHROME,
                        "--headless=new",
                        f"--user-data-dir={profile}",
                        "--hide-scrollbars",
                        "--force-device-scale-factor=1",
                        "--window-size=1200,630",
                        f"--screenshot={target}",
                        f"http://127.0.0.1:{server.server_port}/tools/{name}",
                    ],
                    check=True,
                    capture_output=True,
                    timeout=120,
                )
            finally:
                os.remove(path)
            print(f"assets/share-{language}.png", os.path.getsize(target), "bytes")
    finally:
        server.shutdown()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
