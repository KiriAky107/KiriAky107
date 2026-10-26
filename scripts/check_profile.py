#!/usr/bin/env python3
"""Validate local profile assets before they replace the last good generation."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
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
    "profile/project-notes-articles.svg",
    "profile/project-cpp-acm-notes.svg",
    "profile/project-modern-python-notes.svg",
    "profile/project-opennexus.svg",
    "profile/technologies.svg",
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
    elif path.name.startswith("project-"):
        check_project(root, path.name)
    elif path.name == "technologies.svg":
        check_technologies(root)


def content_catalog() -> dict:
    return json.loads((ROOT / ".github/profile-content.json").read_text(encoding="utf-8"))


def field_text(root: ET.Element, field: str, *, wrapped: bool = False) -> str:
    matches = [element for element in root.iter() if element.get("data-profile-field") == field]
    if len(matches) != 1:
        raise ValueError(f"Expected one visible {field} field in generated card")
    element = matches[0]
    if element.tag.rsplit("}", 1)[-1] != "text":
        raise ValueError(f"Card field is not visible SVG text: {field}")
    lines = [child for child in element if child.tag.rsplit("}", 1)[-1] == "tspan"]
    if wrapped and lines:
        return " ".join("".join(line.itertext()).strip() for line in lines)
    return "".join(element.itertext()).strip()


def check_content_card(root: ET.Element, kind: str) -> None:
    if root.get("data-profile-kind") != kind or root.get("data-profile-ready") != "true":
        raise ValueError(f"The {kind} card did not finish successfully")
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == "foreignObject":
            raise ValueError(f"Expected native SVG for the {kind} card")
        for attribute, value in element.attrib.items():
            if attribute.rsplit("}", 1)[-1] in {"href", "src"} and not value.startswith(("#", "data:")):
                raise ValueError(f"External resource in the {kind} card")


def check_project(root: ET.Element, filename: str) -> None:
    check_content_card(root, "project")
    matches = [project for project in content_catalog()["projects"] if filename == f"project-{project['id']}.svg"]
    if len(matches) != 1:
        raise ValueError(f"Unexpected project card: {filename}")
    project = matches[0]
    if root.get("data-profile-project") != project["id"] or root.get("data-profile-repository") != project["repository"]:
        raise ValueError(f"Project card points to the wrong repository: {filename}")
    if field_text(root, "title") != project["title"]:
        raise ValueError(f"Missing or changed project title: {project['title']}")
    if field_text(root, "description", wrapped=True) != project["description"]:
        raise ValueError(f"Missing or changed English project description: {project['title']}")
    for field in ("stars", "forks"):
        if not re.fullmatch(r"0|[1-9][0-9]*", field_text(root, field)):
            raise ValueError(f"Invalid public {field} count: {project['title']}")
    if field_text(root, "language").lower() in {"", "none", "null", "undefined"}:
        raise ValueError(f"Missing repository language or fallback: {project['title']}")
    updated = field_text(root, "updated")
    if updated != "No pushes yet":
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", updated):
            raise ValueError(f"Invalid repository update date: {project['title']}")
        dt.date.fromisoformat(updated)


def check_technologies(root: ET.Element) -> None:
    check_content_card(root, "technologies")
    catalog = content_catalog()["technology_groups"]
    groups = [element for element in root.iter() if element.get("data-profile-technology-group")]
    if [group.get("data-profile-technology-group") for group in groups] != [group["title"] for group in catalog]:
        raise ValueError("Technology groups are missing or out of order")
    if field_text(root, "title") != "Tools & Technologies":
        raise ValueError("Technology card heading is missing")
    expected_count = sum(len(group["items"]) for group in catalog)
    if root.get("data-profile-count") != str(expected_count):
        raise ValueError("Technology card count does not match the catalog")
    for group, expected in zip(groups, catalog):
        if field_text(group, "group-title") != expected["title"]:
            raise ValueError(f"Missing visible technology group title: {expected['title']}")
        items = [element for element in group.iter() if element.get("data-profile-technology")]
        if [item.get("data-profile-technology") for item in items] != [item["label"] for item in expected["items"]]:
            raise ValueError(f"Missing or reordered technologies in {expected['title']}")
        for item, source in zip(items, expected["items"]):
            if field_text(item, "label") != source["label"] or item.get("data-profile-icon") != source["icon"]:
                raise ValueError(f"Missing technology label or icon: {source['label']}")
            if not any(element.tag.rsplit("}", 1)[-1] == "path" and element.get("d", "").strip() for element in item.iter()):
                raise ValueError(f"Missing vector icon: {source['label']}")


def check_media(root: ET.Element) -> None:
    catalog = json.loads((ROOT / ".github/profile-media.json").read_text(encoding="utf-8"))
    items = [item for section in catalog["sections"] for item in section["items"]]
    expected = [item["title"] for item in items]
    ready = [element for element in root.iter() if element.get("id") == "profile-media"]
    if len(ready) != 1 or ready[0].get("data-profile-ready") != "true":
        raise ValueError("Media render did not finish successfully")
    sections = [element.get("data-profile-section") for element in root.iter() if element.get("data-profile-section")]
    if sections != [section["title"] for section in catalog["sections"]]:
        raise ValueError("Media section headings are missing or out of order")
    entries = [element for element in root.iter() if element.get("data-profile-title")]
    if len(entries) != len(expected) or [entry.get("data-profile-title") for entry in entries] != expected:
        raise ValueError("Media render is missing or changing curated titles")
    if ready[0].get("data-profile-count") != str(len(expected)):
        raise ValueError("Media render count does not match the catalog")
    actual_layouts = [element.get("data-profile-layout") for element in root.iter() if element.get("data-profile-section")]
    if actual_layouts != [section.get("layout", "list") for section in catalog["sections"]]:
        raise ValueError("Media section layouts do not match the catalog")
    for entry, item in zip(entries, items):
        title = item["title"]
        labels = [element for element in entry.iter() if element.get("class") == "media-title"]
        artists = [element for element in entry.iter() if element.get("class") == "media-artist"]
        images = [element for element in entry.iter() if element.tag.rsplit("}", 1)[-1] == "img"]
        if len(labels) != 1 or "".join(labels[0].itertext()) != title or len(images) != 1:
            raise ValueError(f"Missing title or cover: {title}")
        if item.get("artist") and (len(artists) != 1 or "".join(artists[0].itertext()) != "Art by " + item["artist"]):
            raise ValueError(f"Missing artist credit: {title}")
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
    content_height = float(ready[0].get("data-profile-height", "0"))
    if content_height < 100 or not content_height <= height <= content_height + 40:
        raise ValueError(f"Media card height {height} does not fit rendered content {content_height}")


class ReadmeLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.anchors: list[str] = []
        self.links: list[str] = []
        self.images: list[tuple[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a":
            href = values.get("href") or ""
            self.anchors.append(href)
            self.links.append(href)
        elif tag == "img":
            self.images.append((values.get("src") or "", self.anchors[-1] if self.anchors else None))

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.anchors:
            self.anchors.pop()


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
    links = ReadmeLinks()
    links.feed(text)
    projects = content_catalog()["projects"]
    expected_paths = [f"./profile/project-{project['id']}.svg" for project in projects]
    project_images = [(source, href) for source, href in links.images if source in expected_paths]
    if [source for source, _ in project_images] != expected_paths:
        raise ValueError("README project cards are missing or out of order")
    for (_, href), project in zip(project_images, projects):
        if href != project["url"]:
            raise ValueError(f"Missing clickable repository link: {project['title']}")
        if project.get("read_online") and project["read_online"] not in links.links:
            raise ValueError(f"Missing Read online link: {project['title']}")
    if sum(source == "./profile/technologies.svg" for source, _ in links.images) != 1:
        raise ValueError("README must embed the generated technology card once")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated", action="store_true", help="Validate all generated cards")
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
