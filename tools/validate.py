#!/usr/bin/env python3
"""Validate every format pack in the registry and (re)generate index.json.

Zero dependencies: uses the standard-library `tomllib` (Python 3.11+), so it
runs in CI with no toolchain and no access to the app's private crates.

Each pack lives in `formats/<id>/` and has two files:
  - plugin.toml : the installable manifest (exactly what the app consumes)
  - meta.toml   : registry-only metadata (category, tags, maintainer, ...)

What this checks (structural validation):
  * both files parse as TOML
  * plugin `id` is a lowercase slug, matches the folder name, and is unique
  * required fields are present (id, name; per-format name + schema)
  * each detect rule's `hex` is valid (whitespace-insensitive, even # of digits)
  * confidence is 0..=100; endian is "le" or "be"
  * meta has a category and at least one tag

What it does NOT (yet) check: that each embedded `schema` parses under the DSL
grammar. That needs the app's schema parser; it runs client-side at install
time today, and graduates to CI here once the parser crate is published.

Usage:
  python tools/validate.py           # validate all packs, rewrite index.json
  python tools/validate.py --check   # validate + fail if index.json is stale (CI)
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORMATS = ROOT / "formats"
INDEX = ROOT / "index.json"

SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class Problem(Exception):
    pass


def parse_hex(s: str) -> bytes:
    """Mirror the app's parse_hex: whitespace ignored, even digit count."""
    cleaned = re.sub(r"\s+", "", s)
    if len(cleaned) % 2 != 0:
        raise Problem(f"hex has an odd number of digits: {s!r}")
    try:
        return bytes.fromhex(cleaned)
    except ValueError as e:
        raise Problem(f"invalid hex {s!r}: {e}")


def load_toml(path: Path) -> dict:
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        raise Problem(f"missing file: {path.relative_to(ROOT)}")
    except tomllib.TOMLDecodeError as e:
        raise Problem(f"{path.relative_to(ROOT)}: TOML parse error: {e}")


def validate_pack(folder: Path, seen_ids: dict[str, str]) -> dict:
    """Validate one formats/<id>/ pack; return its index entry."""
    manifest = load_toml(folder / "plugin.toml")
    meta = load_toml(folder / "meta.toml")

    pid = manifest.get("id", "")
    if not pid:
        raise Problem(f"{folder.name}/plugin.toml: missing `id`")
    if not SLUG.match(pid):
        raise Problem(f"{folder.name}: id {pid!r} is not a lowercase slug")
    if pid != folder.name:
        raise Problem(f"folder {folder.name!r} must match plugin id {pid!r}")
    if pid in seen_ids:
        raise Problem(f"duplicate id {pid!r} (also in {seen_ids[pid]})")
    seen_ids[pid] = folder.name

    name = manifest.get("name", "")
    if not name:
        raise Problem(f"{pid}: missing `name`")

    formats = manifest.get("formats", [])
    if not formats:
        raise Problem(f"{pid}: declares no [[formats]]")

    fmt_entries = []
    for i, fmt in enumerate(formats):
        fname = fmt.get("name", "")
        if not fname:
            raise Problem(f"{pid}: formats[{i}] missing `name`")
        if not fmt.get("schema", "").strip():
            raise Problem(f"{pid}: format {fname!r} has an empty `schema`")
        conf = fmt.get("confidence", 75)
        if not isinstance(conf, int) or not (0 <= conf <= 100):
            raise Problem(f"{pid}: format {fname!r} confidence must be 0..=100")
        endian = fmt.get("endian", "le")
        if endian not in ("le", "be"):
            raise Problem(f"{pid}: format {fname!r} endian must be le|be")
        detect = fmt.get("detect", [])
        for part in detect:
            parse_hex(part.get("hex", ""))  # raises on bad hex
        fmt_entries.append({
            "name": fname,
            "extension": fmt.get("extension", ""),
            "detects": len(detect) > 0,
            "confidence": conf,
        })

    category = meta.get("category", "")
    tags = meta.get("tags", [])
    if not category:
        raise Problem(f"{pid}/meta.toml: missing `category`")
    if not tags:
        raise Problem(f"{pid}/meta.toml: needs at least one tag")

    return {
        "id": pid,
        "name": name,
        "version": manifest.get("version", ""),
        "description": manifest.get("description", ""),
        "author": manifest.get("author", ""),
        "category": category,
        "tags": tags,
        "formats": fmt_entries,
        "path": f"formats/{pid}/plugin.toml",
    }


def build_index() -> list[dict]:
    if not FORMATS.is_dir():
        return []
    seen: dict[str, str] = {}
    entries = []
    for folder in sorted(p for p in FORMATS.iterdir() if p.is_dir()):
        entries.append(validate_pack(folder, seen))
    return entries


def main() -> int:
    check = "--check" in sys.argv[1:]
    try:
        entries = build_index()
    except Problem as e:
        print(f"validation FAILED: {e}", file=sys.stderr)
        return 1

    catalog = {"version": 1, "count": len(entries), "formats": entries}
    rendered = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"

    if check:
        current = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
        if current != rendered:
            print("index.json is out of date — run: python tools/validate.py",
                  file=sys.stderr)
            return 1
        print(f"OK: {len(entries)} pack(s) valid; index.json is up to date.")
    else:
        INDEX.write_text(rendered, encoding="utf-8")
        print(f"OK: {len(entries)} pack(s) valid; wrote index.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
