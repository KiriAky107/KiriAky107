#!/usr/bin/env python3
"""Generate self-contained project and technology SVGs for the profile workflow."""

from __future__ import annotations

import argparse
from datetime import datetime
from html import escape
import json
from math import ceil
import os
from pathlib import Path
import re
import textwrap
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / ".github/profile-content.json"
ICONS = ROOT / "assets/icons/technology.json"
WIDTH = 480

CSS = """
text { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }
.background { fill: #ffffff; stroke: #d0d7de; }
.surface { fill: #f6f8fc; stroke: #dce1f0; }
.divider { stroke: #e5e8f0; }
.heading, .brand { fill: #5368d6; }
.body { fill: #24292f; }
.muted { fill: #57606a; }
.accent { fill: #7c6bd6; }
.outline { fill: none; stroke: #7c6bd6; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; }
.title { font-size: 20px; font-weight: 600; }
.description { font-size: 15px; }
.metadata { font-size: 12px; }
.group-title { font-size: 15px; font-weight: 600; }
.chip-label { font-size: 14px; font-weight: 500; }
@media (prefers-color-scheme: dark) {
  .background { fill: #0d1117; stroke: #30363d; }
  .surface { fill: #161b22; stroke: #30364b; }
  .divider { stroke: #30363d; }
  .heading, .brand { fill: #8ea8ff; }
  .body { fill: #c9d1d9; }
  .muted { fill: #8b949e; }
  .accent { fill: #a78bfa; }
  .outline { stroke: #a78bfa; }
}
""".strip()

# Simple UI symbols for concepts, rather than brand marks or proficiency scores.
UI_PATHS = {
    "book": "M4 3h13a2 2 0 0 1 2 2v16H6a3 3 0 0 1-3-3V5a2 2 0 0 1 2-2 M7 3v13 M3 17h16",
    "star": "m12 3 2.8 5.7 6.3.9-4.5 4.4 1.1 6.2-5.7-3-5.7 3 1.1-6.2-4.5-4.4 6.3-.9Z",
    "fork": "M6 7v3a3 3 0 0 0 3 3h6a3 3 0 0 0 3-3V7 M12 13v4 M8 5a2 2 0 1 1-4 0 2 2 0 0 1 4 0 M20 5a2 2 0 1 1-4 0 2 2 0 0 1 4 0 M14 19a2 2 0 1 1-4 0 2 2 0 0 1 4 0",
    "calendar": "M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2 M7 3v4 M17 3v4 M3 10h18",
    "search": "M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0 M15 15l6 6 M6 8h5 M6 11h3",
    "vector": "M7 6h10 M7 7l5 11 M17 7l-5 11 M7 5a2 2 0 1 1-4 0 2 2 0 0 1 4 0 M21 5a2 2 0 1 1-4 0 2 2 0 0 1 4 0 M14 20a2 2 0 1 1-4 0 2 2 0 0 1 4 0",
    "agent": "M6 7h12a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3v-8a3 3 0 0 1 3-3 M12 3v4 M9 12v2 M15 12v2 M8 18h8",
    "rag": "M4 3h12v9 M4 3v18h8 M7 7h6 M7 11h4 M19 16a4 4 0 1 1-8 0 4 4 0 0 1 8 0 M18 19l4 3",
    "skill": "M4 4h6l2 2 2-2h6v16h-6l-2 2-2-2H4Z M12 6v16 M7 9h2 M15 9h2 M7 13h2 M15 13h2",
    "plugin": "M8 3v5 M16 3v5 M5 8h14v4a7 7 0 0 1-14 0Z M12 19v3",
}


def attr(value: object) -> str:
    return escape(str(value), quote=True)


def ui_icon(name: str, x: float, y: float, size: int) -> str:
    return f'<g transform="translate({x:g} {y:g}) scale({size / 24:g})"><path class="outline" d="{UI_PATHS[name]}"/></g>'


def svg_document(title: str, description: str, height: int, body: list[str], **metadata: object) -> str:
    attributes = " ".join(f'data-profile-{key.replace("_", "-")}="{attr(value)}"' for key, value in metadata.items())
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="card-title card-description" '
        f'data-profile-ready="true" {attributes}>\n'
        f'<title id="card-title">{attr(title)}</title>\n'
        f'<desc id="card-description">{attr(description)}</desc>\n'
        f'<style>{CSS}</style>\n'
        f'<rect class="background" x=".5" y=".5" width="{WIDTH - 1}" height="{height - 1}" rx="10"/>\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )


def load_sources() -> tuple[dict, dict]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    icons = json.loads(ICONS.read_text(encoding="utf-8"))
    projects = catalog["projects"]
    groups = catalog["technology_groups"]
    if not projects or len({p["id"] for p in projects}) != len(projects):
        raise ValueError("Projects need distinct IDs")
    for project in projects:
        if not re.fullmatch(r"[a-z0-9-]+", project["id"]):
            raise ValueError("Invalid project ID")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", project["repository"]):
            raise ValueError("Invalid GitHub repository name")
        if project["url"] != "https://github.com/" + project["repository"]:
            raise ValueError("Project URL must match its repository")
        if not project["title"] or not project["description"]:
            raise ValueError("Project title and description are required")
    if not groups or len({g["title"] for g in groups}) != len(groups):
        raise ValueError("Technology groups need distinct titles")
    for group in groups:
        if not group["items"]:
            raise ValueError("Technology groups cannot be empty")
        for item in group["items"]:
            if not item["label"] or item["icon"] not in icons.keys() | UI_PATHS.keys():
                raise ValueError(f"Unknown technology icon: {item}")
    for name, icon in icons.items():
        if icon["viewBox"] != "0 0 24 24" or not re.fullmatch(r"[MmZzLlHhVvCcSsQqTtAa0-9eE+.,\s-]+", icon["path"]):
            raise ValueError(f"Unsafe or unsupported SVG icon: {name}")
    return catalog, icons


def fetch_repository(repository: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": "github-profile-cards",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request("https://api.github.com/repos/" + repository, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        raise ValueError(f"GitHub repository lookup failed for {repository}: HTTP {error.code}") from None
    except URLError:
        raise ValueError(f"GitHub repository lookup failed for {repository}") from None


def project_card(project: dict, repository: dict) -> str:
    if repository.get("private") is not False or repository.get("full_name", "").lower() != project["repository"].lower():
        raise ValueError(f"Expected the public repository {project['repository']}")
    for key in ("stargazers_count", "forks_count"):
        if type(repository.get(key)) is not int or repository[key] < 0:
            raise ValueError(f"Invalid {key} for {project['repository']}")
    pushed = repository.get("pushed_at")
    updated = datetime.fromisoformat(pushed.replace("Z", "+00:00")).date().isoformat() if pushed else "No pushes yet"
    language = repository.get("language") or project.get("language_fallback", "Project")
    description_lines = textwrap.wrap(project["description"], width=54, break_long_words=False, break_on_hyphens=False)
    if len(description_lines) == 2:
        first_line = description_lines[0].split()
        while len(description_lines[1]) < 20 and len(first_line) > 1:
            description_lines[1] = first_line.pop() + " " + description_lines[1]
        description_lines[0] = " ".join(first_line)
    if len(description_lines) > 2:
        raise ValueError(f"Project description is too long for its card: {project['id']}")
    body = [
        ui_icon("book", 20, 17, 22),
        f'<text class="heading title" x="52" y="35" data-profile-field="title">{attr(project["title"])}</text>',
        '<text class="body description" data-profile-field="description">',
        *[f'<tspan x="20" y="{63 + index * 21}">{attr(line)}</tspan>' for index, line in enumerate(description_lines)],
        '</text>',
        '<line class="divider" x1="20" y1="100" x2="460" y2="100"/>',
        ui_icon("star", 20, 111, 15),
        f'<text class="muted metadata" x="41" y="123" data-profile-field="stars">{repository["stargazers_count"]}</text>',
        ui_icon("fork", 74, 111, 15),
        f'<text class="muted metadata" x="95" y="123" data-profile-field="forks">{repository["forks_count"]}</text>',
        '<circle class="accent" cx="132" cy="119" r="4"/>',
        f'<text class="muted metadata" x="144" y="123" data-profile-field="language">{attr(language)}</text>',
        ui_icon("calendar", 352, 111, 15),
        f'<text class="muted metadata" x="460" y="123" text-anchor="end" data-profile-field="updated">{updated}</text>',
    ]
    accessible = (f'{project["description"]} Public repository. '
                  f'{repository["stargazers_count"]} stars, {repository["forks_count"]} forks. '
                  f'Language or category: {language}. Last push: {updated}.')
    return svg_document(project["title"], accessible, 143, body,
                        kind="project", project=project["id"], repository=project["repository"])


def technology_card(groups: list[dict], icons: dict) -> str:
    body = [
        '<text class="heading title" x="20" y="35" data-profile-field="title">Tools &amp; Technologies</text>',
        '<line class="divider" x1="20" y1="52" x2="460" y2="52"/>',
    ]
    y = 78
    count = 0
    for group in groups:
        body.append(f'<g data-profile-technology-group="{attr(group["title"])}">')
        body.append(f'<text class="body group-title" x="20" y="{y}" data-profile-field="group-title">{attr(group["title"])}</text>')
        x, chip_y, column = 20, y + 13, 0
        for item in group["items"]:
            # Uppercase acronyms need more room than ordinary mixed-case labels.
            width = 52 + ceil(sum(8.5 if c.isupper() else 4 if c == " " else 7 for c in item["label"]))
            if width > 440:
                raise ValueError("Technology label is too wide")
            if x + width > 460 or column == 4:
                x, chip_y, column = 20, chip_y + 40, 0
            body.append(f'<g data-profile-technology="{attr(item["label"])}" data-profile-icon="{attr(item["icon"])}">')
            body.append(f'<rect class="surface" x="{x}" y="{chip_y}" width="{width}" height="32" rx="7"/>')
            if item["icon"] in icons:
                path = icons[item["icon"]]["path"]
                body.append(f'<path class="brand" transform="translate({x + 11} {chip_y + 7}) scale(.75)" d="{path}"/>')
            else:
                body.append(ui_icon(item["icon"], x + 11, chip_y + 7, 18))
            body.append(f'<text class="body chip-label" x="{x + 37}" y="{chip_y + 21}" data-profile-field="label">{attr(item["label"])}</text>')
            body.append('</g>')
            x += width + 8
            column += 1
            count += 1
        body.append('</g>')
        y = chip_y + 62
    description = "; ".join(group["title"] + ": " + ", ".join(item["label"] for item in group["items"]) for group in groups)
    return svg_document("Tools & Technologies", description, y - 8, body, kind="technologies", count=count)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, help="Previously fetched public repository JSON for an offline preview")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "profile")
    args = parser.parse_args()
    catalog, icons = load_sources()
    snapshot = json.loads(args.metadata.read_text(encoding="utf-8")) if args.metadata else None
    outputs = {}
    for project in catalog["projects"]:
        repository = snapshot[project["repository"]] if snapshot is not None else fetch_repository(project["repository"])
        outputs[f'project-{project["id"]}.svg'] = project_card(project, repository)
    outputs["technologies.svg"] = technology_card(catalog["technology_groups"], icons)
    # Resolve and validate every source before replacing any output.
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for filename, svg in outputs.items():
        (args.output_dir / filename).write_text(svg, encoding="utf-8")
    print(f'Generated {len(outputs)} cards: {len(catalog["projects"])} projects and {sum(len(g["items"]) for g in catalog["technology_groups"])} technologies.')


if __name__ == "__main__":
    main()
