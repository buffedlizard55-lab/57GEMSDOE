#!/usr/bin/env python3
"""Check generated site links and the fail-closed download status."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REQUIRED_PAGES = (
    "index.html",
    "executive-summary.html",
    "method.html",
    "hypotheses.html",
    "results.html",
    "data-sources.html",
    "irregularities.html",
    "run-card.html",
    "research.html",
    "sources.html",
)
FRONT_DOOR_PAGES = ("index.html", "executive-summary.html")
HOLD_TEXT = "HOLD — NOT OK TO DOWNLOAD OR SUBMIT"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        for key, value in attrs:
            if key in ("href", "src") and value:
                self.links.append(value)

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)


def inspect_site(docs: Path = DOCS) -> list[str]:
    docs = docs.resolve()
    errors: list[str] = []
    parsed: dict[str, tuple[str, list[str]]] = {}

    for relative in REQUIRED_PAGES:
        page = docs / relative
        if not page.is_file():
            errors.append(f"missing generated page: {relative}")
            continue
        parser = LinkParser()
        source = page.read_text(encoding="utf-8")
        parser.feed(source)
        parsed[relative] = ("".join(parser.text_parts), parser.links)
        if relative in FRONT_DOOR_PAGES and HOLD_TEXT not in source:
            errors.append(f"front-door page lacks prominent HOLD status: {relative}")

        for href in parser.links:
            url = urlsplit(href)
            if url.scheme or url.netloc or not url.path:
                continue
            target_name = unquote(url.path)
            if target_name.lower().endswith((".tif", ".tiff", ".zip")) or "downloads/" in target_name.lower():
                errors.append(f"active download link is forbidden on {relative}: {href}")
            target = (page.parent / target_name).resolve()
            try:
                target.relative_to(docs)
            except ValueError:
                errors.append(f"internal link escapes the published docs tree on {relative}: {href}")
                continue
            if not target.is_file():
                errors.append(f"broken internal link on {relative}: {href}")

    return errors


def main() -> int:
    errors = inspect_site()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(f"PASS: {len(REQUIRED_PAGES)} generated pages, internal links resolve, HOLD is prominent, no active download links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
