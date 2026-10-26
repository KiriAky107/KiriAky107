#!/usr/bin/env python3
"""Build a self-contained lowlighter/metrics preset from the curated media list."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / ".github/profile-media.json"

# This stylesheet is added after Metrics' own stylesheet. Keep it independent
# of plugin classes, which may be removed before extras_js creates the gallery.
CSS = """.items-wrapper { margin: 0; padding: 0; }
#profile-media {
  --media-text: #24292f;
  --media-accent: #5368d6;
  --media-border: #d0d7de;
  --media-surface: #f6f8fc;
  color: var(--media-text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  box-sizing: border-box;
  padding: 12px 14px 8px;
  width: 480px;
}
#profile-media * { box-sizing: border-box; }
#profile-media .media-section { margin: 0; padding: 0; }
#profile-media .media-section + .media-section { margin-top: 26px; }
#profile-media .media-heading {
  margin: 0 0 12px;
  padding: 0 0 10px;
  border-bottom: 1px solid var(--media-border);
  color: var(--media-accent);
  font-size: 23px;
  font-weight: 600;
  line-height: 30px;
}
#profile-media .media-list { display: flex; flex-direction: column; gap: 10px; }
#profile-media .media-entry {
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 70px;
}
#profile-media .media-cover {
  display: block;
  width: 50px;
  height: 70px;
  flex: 0 0 50px;
  object-fit: contain;
  border-radius: 5px;
  background: var(--media-surface);
}
#profile-media .media-title {
  color: var(--media-text);
  font-size: 18px;
  font-weight: 500;
  line-height: 26px;
  white-space: normal;
  overflow-wrap: anywhere;
}
@media (prefers-color-scheme: dark) {
  #profile-media {
    --media-text: #c9d1d9;
    --media-accent: #8ea8ff;
    --media-border: #30363d;
    --media-surface: #161b22;
  }
}
""".strip()

SCRIPT = """
const catalog = __CATALOG__;
const target = document.querySelector('.items-wrapper');
if (!target) throw new Error('Metrics content container is missing');
const xhtml = 'http://www.w3.org/1999/xhtml';
const element = (tag, className) => {
  const node = document.createElementNS(xhtml, tag);
  if (className) node.setAttribute('class', className);
  return node;
};
const gallery = element('div');
gallery.id = 'profile-media';
const images = [];
for (const group of catalog.sections) {
  const section = element('section', 'media-section');
  section.setAttribute('data-profile-section', group.title);
  const heading = element('h2', 'media-heading');
  heading.textContent = group.title;
  section.append(heading);
  const list = element('div', 'media-list');
  for (const item of group.items) {
    const entry = element('div', 'media-entry');
    entry.setAttribute('data-profile-title', item.title);
    const cover = element('img', 'media-cover');
    cover.setAttribute('src', item.image);
    cover.setAttribute('alt', item.title + ' cover');
    cover.setAttribute('width', '50');
    cover.setAttribute('height', '70');
    const title = element('span', 'media-title');
    title.textContent = item.title;
    entry.append(cover, title);
    list.append(entry);
    images.push(cover);
  }
  section.append(list);
  gallery.append(section);
}
target.replaceChildren(gallery);
await Promise.all(images.map(image => image.decode()));
if (images.some(image => !image.complete || image.naturalWidth === 0)) {
  throw new Error('A media cover did not decode');
}
// Metrics catches extras_js exceptions, so validation requires this final marker.
gallery.setAttribute('data-profile-ready', 'true');
gallery.setAttribute('data-profile-count', String(images.length));
""".strip()


def load_catalog() -> dict:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    sections = catalog.get("sections", [])
    if [section.get("title") for section in sections] != ["Anime", "Visual Novels"]:
        raise ValueError("Expected Anime and Visual Novels sections in that order")
    if [len(section.get("items", [])) for section in sections] != [6, 7]:
        raise ValueError("Expected six anime and seven visual novels")
    for section in sections:
        titles = [item.get("title") for item in section["items"]]
        if len(set(titles)) != len(titles) or not all(titles):
            raise ValueError(f"Missing or duplicate title in {section['title']}")
        for item in section["items"]:
            if urlparse(item["url"]).scheme != "https":
                raise ValueError(f"Expected an HTTPS title link: {item['title']}")
            path = (ROOT / item["cover"]).resolve()
            if not path.is_relative_to(ROOT / "assets/covers") or not path.is_file():
                raise ValueError(f"Missing local cover: {item['cover']}")
    return catalog


def build_preset(catalog: dict) -> dict:
    embedded = {"sections": []}
    for section in catalog["sections"]:
        group = {"title": section["title"], "items": []}
        for item in section["items"]:
            path = ROOT / item["cover"]
            mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(path.suffix.lower())
            if mime is None:
                raise ValueError(f"Unsupported cover format: {path.name}")
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            group["items"].append({"title": item["title"], "image": f"data:{mime};base64,{encoded}"})
        embedded["sections"].append(group)
    payload = json.dumps(embedded, ensure_ascii=True, separators=(",", ":"))
    return {"schema": "v1", "with": {"extras_css": CSS, "extras_js": SCRIPT.replace("__CATALOG__", payload)}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="JSON preset for Metrics' local /renders mount")
    args = parser.parse_args()
    preset = build_preset(load_catalog())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(preset, ensure_ascii=False), encoding="utf-8")
    print(f"Prepared 13 embedded covers in {args.output.name} ({args.output.stat().st_size:,} bytes).")


if __name__ == "__main__":
    main()
