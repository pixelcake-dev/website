"""Checks what a shared link to each page shows: every tag is there, the picture is
named by its whole https address and is a card of the page's own language,
1200 x 630 and under 300 kB, and each page has a description of its own.

    python tools/check-previews.py

Prints what it finds on each page and ends with an error when anything is wrong.
"""

import html.parser
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["index.html", "why.html", "privacy.html", "it/index.html", "it/why.html", "it/privacy.html"]
SITE = "https://pixelcake.dev/"
LOCALES = {"en": ("en_GB", "it_IT"), "it": ("it_IT", "en_GB")}

PROPERTIES = [
    "og:type", "og:site_name", "og:locale", "og:locale:alternate", "og:url", "og:title", "og:description",
    "og:image", "og:image:width", "og:image:height", "og:image:type", "og:image:alt",
]
NAMES = ["description", "twitter:card", "twitter:title", "twitter:description", "twitter:image", "twitter:image:alt"]


class Head(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.lang, self.canonical = {}, None, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "meta":
            key = a.get("property") or a.get("name")
            if key:
                self.tags.setdefault(key, []).append(a.get("content") or "")
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def main():
    problems, descriptions = [], {}
    for page in PAGES:
        head = Head()
        with open(os.path.join(ROOT, page), encoding="utf-8") as f:
            head.feed(f.read())
        language = head.lang
        said = lambda key: (head.tags.get(key) or [""])[0]  # noqa: E731
        found = []

        def wrong(text):
            problems.append(f"{page}: {text}")
            found.append("WRONG " + text)

        for key in PROPERTIES + NAMES:
            values = head.tags.get(key, [])
            if len(values) != 1 or not values[0].strip():
                wrong(f"{key}: {len(values)} times" if values else f"{key} missing")
        if said("twitter:card") != "summary_large_image":
            wrong(f"twitter:card is «{said('twitter:card')}»")
        if said("og:site_name") != "PixelCake":
            wrong(f"og:site_name is «{said('og:site_name')}»")
        if language not in LOCALES:
            wrong(f"<html lang> is «{language}»")
        elif (said("og:locale"), said("og:locale:alternate")) != LOCALES[language]:
            wrong(f"og:locale {said('og:locale')} / {said('og:locale:alternate')} for a page in «{language}»")
        # (a home page is named by its folder: https://pixelcake.dev/it/)
        address = SITE + (page[: -len("index.html")] if page.endswith("index.html") else page)
        if said("og:url") != address:
            wrong(f"og:url {said('og:url')} is not the address of the page, {address}")
        if head.canonical != address:
            wrong(f"the canonical address {head.canonical} is not {address}")
        if said("og:image:width") != "1200" or said("og:image:height") != "630" or said("og:image:type") != "image/png":
            wrong("og:image size or type is not 1200 x 630 PNG")

        for key in ("og:image", "twitter:image"):
            image = said(key)
            if not image.startswith(SITE):
                wrong(f"{key} «{image}» is not a whole https address of the site")
                continue
            if image != f"{SITE}assets/share-{language}.png":
                wrong(f"{key} is {image}, not the card of «{language}»")
            path = os.path.join(ROOT, *image[len(SITE):].split("/"))
            if not os.path.exists(path):
                wrong(f"{key}: no file {image[len(SITE):]}")
                continue
            size, weight = png_size(path), os.path.getsize(path)
            if size != (1200, 630):
                wrong(f"{key}: the picture is {size}, not 1200 x 630")
            if weight > 300 * 1024:
                wrong(f"{key}: the picture is {weight // 1024} kB, over 300")
        if said("og:image:alt") != said("twitter:image:alt"):
            wrong("og:image:alt and twitter:image:alt differ")

        description = said("description")
        if description in descriptions:
            wrong(f"the same description as {descriptions[description]}")
        descriptions[description] = page

        card = said("og:image")
        weight = os.path.getsize(os.path.join(ROOT, *card[len(SITE):].split("/"))) if card.startswith(SITE) and os.path.exists(os.path.join(ROOT, *card[len(SITE):].split("/"))) else 0
        print(f"{page:17} {language}  {said('og:locale'):6} {card[len(SITE):]:22} {weight // 1024:>3} kB  «{said('og:title')}»")
        for line in found:
            print("    " + line)

    if problems:
        print(f"\n{len(problems)} problems")
        return 1
    print(f"\n{len(PAGES)} pages: every tag there, every card of its own language, 1200 x 630, under 300 kB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
