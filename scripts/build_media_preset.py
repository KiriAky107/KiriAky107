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
  --media-muted: #57606a;
  color: var(--media-text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, 'Noto Sans CJK SC', 'Noto Sans SC', 'Microsoft YaHei', 'PingFang SC', sans-serif;
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
  min-width: 0;
  white-space: normal;
  overflow-wrap: anywhere;
}
#profile-media .media-list.compact {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 14px;
}
#profile-media .compact .media-entry { min-height: 60px; gap: 10px; }
#profile-media .compact .media-cover { width: 42px; height: 60px; flex-basis: 42px; }
#profile-media .compact .media-title { font-size: 16px; line-height: 23px; }
#profile-media .media-list.characters {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px 14px;
}
#profile-media .characters .media-entry {
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  min-width: 0;
}
#profile-media .characters .media-cover {
  width: 100%;
  height: 219px;
  flex-basis: 219px;
  object-fit: contain;
  border-radius: 8px;
}
#profile-media .characters .media-title {
  font-size: 16px;
  line-height: 23px;
  text-align: left;
  padding: 0 2px;
}
#profile-media .media-artist {
  display: block;
  margin-top: -4px;
  padding: 0 2px;
  color: var(--media-muted);
  font-size: 12px;
  line-height: 18px;
  overflow-wrap: anywhere;
}
@media (prefers-color-scheme: dark) {
  #profile-media {
    --media-text: #c9d1d9;
    --media-accent: #8ea8ff;
    --media-border: #30363d;
    --media-surface: #161b22;
    --media-muted: #8b949e;
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
  section.setAttribute('data-profile-layout', group.layout);
  const heading = element('h2', 'media-heading');
  heading.textContent = group.title;
  section.append(heading);
  const list = element('div', 'media-list');
  list.classList.add(group.layout);
  for (const item of group.items) {
    const entry = element('div', 'media-entry');
    entry.setAttribute('data-profile-title', item.title);
    const cover = element('img', 'media-cover');
    cover.setAttribute('src', item.image);
    cover.setAttribute('alt', item.title + (group.layout === 'characters' ? ' art by ' + item.artist : ' cover'));
    cover.setAttribute('width', group.layout === 'characters' ? '219' : group.layout === 'compact' ? '42' : '50');
    cover.setAttribute('height', group.layout === 'characters' ? '219' : group.layout === 'compact' ? '60' : '70');
    const title = element('span', 'media-title');
    title.textContent = item.title;
    entry.append(cover, title);
    if (item.artist) {
      const artist = element('span', 'media-artist');
      artist.textContent = 'Art by ' + item.artist;
      entry.append(artist);
    }
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
if (document.fonts) await document.fonts.ready;
// Metrics catches extras_js exceptions, so validation requires this final marker.
gallery.setAttribute('data-profile-ready', 'true');
gallery.setAttribute('data-profile-count', String(images.length));
gallery.setAttribute('data-profile-height', String(Math.ceil(gallery.getBoundingClientRect().height)));
""".strip()


def load_catalog() -> dict:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    sections = catalog.get("sections", [])
    section_titles = [section.get("title") for section in sections]
    if not sections or not all(section_titles) or len(set(section_titles)) != len(sections):
        raise ValueError("Expected nonempty sections with distinct titles")
    for section in sections:
        if section.get("layout", "list") not in {"list", "compact", "characters"}:
            raise ValueError(f"Unknown layout for {section['title']}")
        titles = [item.get("title") for item in section["items"]]
        if not titles or len(set(titles)) != len(titles) or not all(titles):
            raise ValueError(f"Missing or duplicate title in {section['title']}")
        for item in section["items"]:
            if urlparse(item["url"]).scheme != "https":
                raise ValueError(f"Expected an HTTPS title link: {item['title']}")
            if section.get("layout") == "characters":
                if not item.get("artist") or urlparse(item.get("source", "")).scheme != "https":
                    raise ValueError(f"Missing artist or artwork source: {item['title']}")
            path = (ROOT / item["cover"]).resolve()
            if not path.is_relative_to(ROOT / "assets/covers") or not path.is_file():
                raise ValueError(f"Missing local cover: {item['cover']}")
    return catalog


def build_preset(catalog: dict) -> dict:
    embedded = {"sections": []}
    for section in catalog["sections"]:
        group = {"title": section["title"], "layout": section.get("layout", "list"), "items": []}
        for item in section["items"]:
            path = ROOT / item["cover"]
            mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(path.suffix.lower())
            if mime is None:
                raise ValueError(f"Unsupported cover format: {path.name}")
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            embedded_item = {"title": item["title"], "image": f"data:{mime};base64,{encoded}"}
            if item.get("artist"):
                embedded_item["artist"] = item["artist"]
            group["items"].append(embedded_item)
        embedded["sections"].append(group)
    payload = json.dumps(embedded, ensure_ascii=True, separators=(",", ":"))
    return {"schema": "v1", "with": {"extras_css": CSS, "extras_js": SCRIPT.replace("__CATALOG__", payload)}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="JSON preset for Metrics' local /renders mount")
    args = parser.parse_args()
    catalog = load_catalog()
    preset = build_preset(catalog)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(preset, ensure_ascii=False), encoding="utf-8")
    count = sum(len(section["items"]) for section in catalog["sections"])
    print(f"Prepared {count} embedded images in {args.output.name} ({args.output.stat().st_size:,} bytes).")


if __name__ == "__main__":
    main()
