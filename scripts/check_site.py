#!/usr/bin/env python3
"""Build/check the HOLD-first Pages site without downloads, experiments, or model work."""
from __future__ import annotations

import argparse
import json
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
    "archive.html",
    "h57k.html",
    "session-3.html",
    "session-4.html",
)
FRONT_DOOR_PAGES = ("index.html", "executive-summary.html")
HOLD_TEXT = "HOLD — NOT OK TO DOWNLOAD OR SUBMIT"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.download_links: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.add(attributes["id"])
        for key in ("href", "src"):
            value = attributes.get(key)
            if value:
                self.links.append(value)
        if tag == "a" and "download" in attributes:
            self.download_links.append(attributes.get("href", ""))


def _is_download_path(value: str) -> bool:
    path = urlsplit(value).path.lower()
    return (path.endswith((".tif", ".tiff", ".zip"))
            or "downloads/" in path or path.startswith("downloads/"))


def inspect_site(docs: Path = DOCS) -> list[str]:
    """Validate every published HTML page and reject active raster/ZIP links."""
    docs = docs.resolve()
    errors: list[str] = []
    pages = sorted(docs.rglob("*.html"))
    if not pages:
        return ["no HTML pages found in published site"]

    for relative in REQUIRED_PAGES:
        if not (docs / relative).is_file():
            errors.append(f"missing required generated page: {relative}")

    for page in pages:
        source = page.read_text(encoding="utf-8")
        parser = LinkParser()
        parser.feed(source)
        rel = page.relative_to(docs).as_posix()
        if HOLD_TEXT not in source:
            errors.append(f"published page lacks HOLD status: {rel}")
        if rel in FRONT_DOOR_PAGES:
            first_content_heading = source.find("<h2>")
            visible_intro = source if first_content_heading < 0 else source[:first_content_heading]
            if HOLD_TEXT not in visible_intro:
                errors.append(f"front-door page lacks prominent first-viewport HOLD status: {rel}")
        if parser.download_links:
            errors.append(f"active HTML download attribute on {rel}: {parser.download_links}")

        for href in parser.links:
            if _is_download_path(href):
                errors.append(f"active TIFF/ZIP download link on {rel}: {href}")
            url = urlsplit(href)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (page.parent / unquote(url.path)).resolve()
            try:
                target.relative_to(docs)
            except ValueError:
                errors.append(f"local link escapes published site on {rel}: {href}")
                continue
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                errors.append(f"broken local link on {rel}: {href}")
                continue
            if url.fragment and target.suffix.lower() == ".html":
                target_parser = LinkParser()
                target_parser.feed(target.read_text(encoding="utf-8"))
                if unquote(url.fragment) not in target_parser.ids:
                    errors.append(f"missing local anchor on {rel}: {href}")

    return errors


def check(root: Path = ROOT) -> dict:
    """Check HOLD status, matching run-card copies, links, and no download links."""
    root = Path(root).resolve()
    errors = inspect_site(root / "docs")
    card_path = root / "evidence" / "run_card.json"
    current_path = root / "evidence" / "run_card_current.json"
    public_path = root / "docs" / "data" / "run_card.json"
    public_current_path = root / "docs" / "data" / "run_card_current.json"
    irregularities_path = root / "evidence" / "irregularities_current.json"
    public_irregularities_path = root / "docs" / "data" / "irregularities_current.json"
    hypotheses_path = root / "evidence" / "hypotheses_current.json"
    public_hypotheses_path = root / "docs" / "data" / "hypotheses_current.json"
    for path in (public_path, public_current_path, public_irregularities_path, public_hypotheses_path):
        if path.is_file() and not path.read_bytes().endswith(b"\n"):
            errors.append(f"public JSON must end with a newline: {path.relative_to(root)}")
    try:
        card = json.loads(card_path.read_text(encoding="utf-8"))
        current = json.loads(current_path.read_text(encoding="utf-8"))
        public = json.loads(public_path.read_text(encoding="utf-8"))
        public_current = json.loads(public_current_path.read_text(encoding="utf-8"))
        irregularities = json.loads(irregularities_path.read_text(encoding="utf-8"))
        public_irregularities = json.loads(public_irregularities_path.read_text(encoding="utf-8"))
        hypotheses = json.loads(hypotheses_path.read_text(encoding="utf-8"))
        public_hypotheses = json.loads(public_hypotheses_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"current audit JSON missing or invalid: {exc}")
        card = current = public = public_current = irregularities = public_irregularities = {}
        hypotheses = public_hypotheses = {}

    current_card_consistent = bool(card) and card == current == public == public_current
    if not current_card_consistent:
        errors.append("current run-card copies differ")
    if not irregularities or irregularities != public_irregularities:
        errors.append("current irregularities ledger and public copy differ")
    if not hypotheses or hypotheses != public_hypotheses:
        errors.append("ranked hypothesis evidence and public copy differ")
    candidates = hypotheses.get("candidates", [])
    ranks = [row.get("rank") for row in candidates if isinstance(row, dict)]
    if not (3 <= len(candidates) <= 5 and ranks == list(range(1, len(candidates) + 1))):
        errors.append("current hypothesis list must contain 3–5 consecutively ranked candidates")
    if any("NOT RUN" not in str(row.get("status", "NOT RUN")).upper()
           and "UNTRIED" not in str(row.get("status", "")).upper()
           for row in candidates if isinstance(row, dict)):
        errors.append("a candidate in the untried shortlist is mislabeled as run")
    irregularities_text = json.dumps(irregularities, ensure_ascii=False).lower()
    if "download is permitted for research" in irregularities_text:
        errors.append("current irregularities ledger still claims research download permission")

    withdrawn_receipt_paths = (
        root / "docs/downloads/gems57-h57i-iso_full-20261009T202310Z-5e393d50e59a-zeros.json",
        root / "docs/downloads/checks-gems57-h57i-iso_full-20261009T202310Z-5e393d50e59a-zeros.tif.json",
        root / "docs/downloads/archive/run_card.json",
    )
    public_receipts_withdrawn = True
    for receipt_path in withdrawn_receipt_paths:
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            archived_name = receipt.get("archived_original_receipt", receipt.get("archived_original_card"))
            archived = root / archived_name if archived_name else None
            okay = (
                receipt.get("current_audit_status") == HOLD_TEXT
                and str(receipt.get("current_download_status", "")).startswith("NOT OK")
                and str(receipt.get("current_submission_status", "")).startswith("NOT OK")
                and receipt.get("verdict") != "promote"
                and archived is not None and archived.is_file()
            )
        except (OSError, json.JSONDecodeError):
            okay = False
        if not okay:
            public_receipts_withdrawn = False
            errors.append(f"historical public receipt lacks a withdrawal notice/original: {receipt_path.relative_to(root)}")

    session4_path = root / "evidence" / "run_card_session4.json"
    session4_original = root / "evidence" / "run_card_legacy_h57i.json"
    try:
        session4 = json.loads(session4_path.read_text(encoding="utf-8"))
        session4_withdrawn = (
            session4.get("current_audit_status") == HOLD_TEXT
            and session4.get("verdict") == "negative"
            and session4.get("promote") is False
            and session4.get("preserved_original") == "evidence/run_card_legacy_h57i.json"
            and session4_original.is_file()
        )
    except (OSError, json.JSONDecodeError):
        session4_withdrawn = False
    if not session4_withdrawn:
        errors.append("non-legacy session-4 run-card path still lacks a withdrawal notice")

    retired_publisher = root / "scripts" / "build_site_session4.py"
    if not retired_publisher.is_file() or "Retired" not in retired_publisher.read_text(encoding="utf-8"):
        errors.append("unsafe session-4 site publisher is not retired")
    retired_session2 = root / "scripts" / "build_r2_submission.py"
    if (not retired_session2.is_file()
            or "no-output stub" not in retired_session2.read_text(encoding="utf-8")):
        errors.append("session-2 publisher that screened after placement is not retired")

    status_ok = (
        card.get("okay_to_download") is False
        and card.get("okay_to_submit") is False
        and card.get("verdict") == "negative"
        and card.get("promote") is False
        and card.get("submission_slots_used") == 0
        and card.get("download_status", "").startswith("NOT OK")
    )
    if not status_ok:
        errors.append("current run card does not encode the required negative HOLD")
    witness = card.get("registry_comparison", {}).get("independent_witness_blocker", {})
    if (witness.get("universal_overlap_blocker") is not True
            or witness.get("uncovered_allowable_cells") != 0
            or witness.get("sha256") != "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be"):
        errors.append("current run card does not record the independently verified universal-overlap witness")
    historical = card.get("historical_artifact_review", {})
    if (historical.get("okay_to_download") is not False
            or historical.get("okay_to_submit") is not False
            or historical.get("receipt_hash_size_and_zip_match_current_bytes") is not True
            or historical.get("format_review", {}).get("all_finite") is not True):
        errors.append("historical lean-offset artifact review is missing or misstates clearance")
    final_dots = card.get("final_dots", {})
    if final_dots.get("status") != "not_generated":
        errors.append("final dots must remain ungenerated after the pre-placement stop")

    report = card.get("registry_comparison", {})
    cache = report.get("current_cache_preflight", {})
    expected = report.get("indexed_matching_grid_rasters")
    # Either the pre-session 0/679 HOLD state, or a session-6 verified state that must
    # agree with the measured profile evidence. Both keep HOLD; neither clears a candidate.
    incomplete_ok = (
        cache.get("status") == "HOLD / INCOMPLETE"
        and cache.get("verified_rasters") == 0
        and cache.get("missing_cache_files") == expected
    )
    verified_ok = False
    profile_path = root / "evidence" / "registry_profile_session6.json"
    try:
        profile_summary = json.loads(profile_path.read_text(encoding="utf-8"))["summary"]
        verified_ok = (
            str(cache.get("status", "")).startswith("VERIFIED")
            and cache.get("verified_rasters") == expected == profile_summary["indexed"] == 679
            and cache.get("missing_cache_files") == profile_summary["errors"] == 0
            and cache.get("sha256_mismatches") == profile_summary["sha256_pin_mismatches"] == 0
            and cache.get("git_blob_sha1_mismatches") == profile_summary["git_blob_sha1_mismatches"] == 0
        )
    except (OSError, json.JSONDecodeError, KeyError):
        verified_ok = False
    cache_ok = (incomplete_ok or verified_ok) and expected == 679
    if not cache_ok:
        errors.append("current 679-raster cache preflight is neither the recorded 0/679 HOLD state nor a verified state matching evidence/registry_profile_session6.json")
    if "not organizer-complete" not in str(card.get("registry_scope", "")).lower():
        errors.append("current run card overstates or omits the public registry's non-organizer-complete scope")
    audit_scope_path = root / "registry" / "audit_scope.json"
    try:
        audit_scope = json.loads(audit_scope_path.read_text(encoding="utf-8"))
        limitations = " ".join(str(x) for x in audit_scope.get("limitations", [])).lower()
        if "not a complete organizer registry" not in limitations:
            errors.append("pinned registry scope must disclose that it is not an organizer-complete registry")
    except (OSError, json.JSONDecodeError):
        errors.append("pinned registry audit-scope disclosure is missing or invalid")

    if errors:
        raise AssertionError("\n".join(errors))
    html_pages = list((root / "docs").rglob("*.html"))
    return {
        "pages_checked": len(html_pages),
        "links_pass": True,
        "active_download_links": 0,
        "current_card_consistent": current_card_consistent,
        "current_irregularities_consistent": irregularities == public_irregularities,
        "current_hypotheses_consistent": hypotheses == public_hypotheses,
        "universal_overlap_blocker_recorded": True,
        "public_receipts_withdrawn": public_receipts_withdrawn,
        "session4_withdrawn": session4_withdrawn,
        "current_status": "HOLD — NOT OK TO DOWNLOAD OR SUBMIT",
        "cache_preflight": f"{cache.get('verified_rasters')}/{expected} verified",
        "final_dots": "not generated",
        "submission_cleared": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true", help="regenerate the site before checking")
    args = parser.parse_args()
    if args.build:
        import sys
        sys.path.insert(0, str(ROOT))
        from scripts import build_site
        build_site.main()
    result = check()
    print(f"PASS: {result['pages_checked']} HTML pages; internal links resolve; HOLD is prominent; "
          "no active download links; current cards/ledger/hypotheses are consistent; historical receipts and unsafe publisher are withdrawn; "
          "universal overlap blocker recorded; "
          f"{result['cache_preflight']} cache")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
