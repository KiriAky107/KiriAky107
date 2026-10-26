#!/usr/bin/env python3
"""Validate local profile assets before they replace the last good generation."""

from __future__ import annotations

import argparse
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
    parser.add_argument("--generated", action="store_true", help="Validate the seven generated cards")
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
