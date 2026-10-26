#!/usr/bin/env python3
"""Validate local profile assets before they replace the last good generation."""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = (
    "profile/stats-light.svg",
    "profile/stats-dark.svg",
    "profile/top-langs-light.svg",
    "profile/top-langs-dark.svg",
    "profile/snake-light.svg",
    "profile/snake-dark.svg",
    "profile-3d-contrib/profile-custom.svg",
    "profile/media.svg",
)
ERROR_MESSAGES = (
    "something went wrong",
    "resource not accessible by integration",
    "could not fetch",
    "invalid username",
    "rate limit exceeded",
    "bad credentials",
)


def check_svg(relative: str) -> None:
    path = ROOT / relative
    if not path.is_file():
        raise ValueError(f"Missing generated asset: {relative}")
    text = path.read_text(encoding="utf-8")
    if len(text) < 100:
        raise ValueError(f"Empty or incomplete SVG: {relative}")
    if any(message in text.lower() for message in ERROR_MESSAGES):
        raise ValueError(f"Error card detected; refusing to publish: {relative}")
    root = ET.fromstring(text)
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError(f"Not a valid SVG document: {relative}")
    if not root.get("viewBox") and not (root.get("width") and root.get("height")):
        raise ValueError(f"SVG has no dimensions: {relative}")
    if any(element.tag.rsplit("}", 1)[-1] == "script" for element in root.iter()):
        raise ValueError(f"Executable script in SVG: {relative}")
    if path.name == "media.svg":
        check_media(root)


def check_media(root: ET.Element) -> None:
    catalog = json.loads((ROOT / ".github/profile-media.json").read_text(encoding="utf-8"))
    expected = [item["title"] for section in catalog["sections"] for item in section["items"]]
    ready = [element for element in root.iter() if element.get("id") == "profile-media"]
    if len(ready) != 1 or ready[0].get("data-profile-ready") != "true":
        raise ValueError("Media render did not finish successfully")
    sections = [element.get("data-profile-section") for element in root.iter() if element.get("data-profile-section")]
    if sections != [section["title"] for section in catalog["sections"]]:
        raise ValueError("Media section headings are missing or out of order")
    entries = [element for element in root.iter() if element.get("data-profile-title")]
    if len(entries) != 13 or [entry.get("data-profile-title") for entry in entries] != expected:
        raise ValueError("Media render is missing or changing curated titles")
    for entry, title in zip(entries, expected):
        labels = [element for element in entry.iter() if element.get("class") == "media-title"]
        images = [element for element in entry.iter() if element.tag.rsplit("}", 1)[-1] == "img"]
        if len(labels) != 1 or "".join(labels[0].itertext()) != title or len(images) != 1:
            raise ValueError(f"Missing title or cover: {title}")
        source = images[0].get("src", "")
        if not source.startswith(("data:image/jpeg;base64,", "data:image/png;base64,")):
            raise ValueError(f"Cover is not embedded: {title}")
        decoded = base64.b64decode(source.split(",", 1)[1], validate=True)
        if len(decoded) < 100:
            raise ValueError(f"Empty embedded cover: {title}")
    if root.get("viewBox"):
        height = float(root.get("viewBox").split()[-1])
    else:
        height = float(root.get("height", "0").removesuffix("px"))
    if not 1000 <= height <= 1600:
        raise ValueError(f"Unexpected media card height: {height}")


def check_readme() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for relative in re.findall(r'(?:src|srcset)="(\./[^"?#]+)"', text):
        path = ROOT / relative
        if not path.is_file():
            raise ValueError(f"Broken local image reference: {relative}")
        if path.suffix == ".svg":
            check_svg(relative)
    if "style=" in text:
        raise ValueError("README contains inline styles stripped by GitHub")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated", action="store_true", help="Validate all eight generated cards")
    parser.add_argument("--readme", action="store_true", help="Also check README local references")
    args = parser.parse_args()
    try:
        if args.generated or not args.readme:
            for relative in GENERATED:
                check_svg(relative)
        if args.readme:
            check_readme()
    except (OSError, ValueError, ET.ParseError) as error:
        print(f"Profile validation failed: {error}", file=sys.stderr)
        return 1
    print("Profile assets validated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
