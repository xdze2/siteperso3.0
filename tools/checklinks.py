#!/usr/bin/env python3
"""Check for broken links in the site.

Usage: tools/checklinks.py [--external] [--inbox]

Checks local href/src (file exists, #anchor exists in target html).
--external also HEAD/GET-checks http(s) links (slow).
inbox/ is skipped unless --inbox is given; sources/ dirs are always skipped.
Exit code 1 if something is broken.
"""
import sys
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent.parent
SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:")


class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []  # (line, url)
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("name"):
            self.ids.add(a["name"])
        for key in ("href", "src"):
            if a.get(key):
                self.links.append((self.getpos()[0], a[key].strip()))
        if a.get("srcset"):
            for part in a["srcset"].split(","):
                if part.strip():
                    self.links.append((self.getpos()[0], part.split()[0]))


def parse(path, cache={}):
    if path not in cache:
        p = Parser()
        p.feed(path.read_text(encoding="utf-8", errors="replace"))
        cache[path] = p
    return cache[path]


def check_external(url):
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": "Mozilla/5.0 checklinks"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return None
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}"
        except Exception as e:
            err = type(e).__name__
    return err


def main():
    external = "--external" in sys.argv
    inbox = "--inbox" in sys.argv
    broken = 0
    seen_ext = {}

    for page in sorted(ROOT.rglob("*.html")):
        rel = page.relative_to(ROOT)
        if rel.parts[0] == "inbox" and not inbox:
            continue
        if "sources" in rel.parts:  # saved pages, not part of the site
            continue
        for line, url in parse(page).links:
            if not url or url.startswith(SKIP_SCHEMES):
                continue
            if url.startswith(("http://", "https://", "//")):
                if external:
                    if url not in seen_ext:
                        seen_ext[url] = check_external("https:" + url if url.startswith("//") else url)
                    if seen_ext[url]:
                        print(f"{rel}:{line}: {url} ({seen_ext[url]})")
                        broken += 1
                continue
            parts = urlsplit(url)
            path = unquote(parts.path)
            if path.startswith("/"):
                target = ROOT / path.lstrip("/")
            else:
                target = page.parent / path if path else page
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                print(f"{rel}:{line}: {url} (missing file)")
                broken += 1
                continue
            if parts.fragment and target.suffix == ".html" and parts.fragment != "top":
                if unquote(parts.fragment) not in parse(target).ids:
                    print(f"{rel}:{line}: {url} (missing anchor)")
                    broken += 1

    print(f"{broken} broken link(s)")
    sys.exit(1 if broken else 0)


if __name__ == "__main__":
    main()
