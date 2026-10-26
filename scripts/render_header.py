#!/usr/bin/env python3
"""Render the profile's two native SVG headers with no external dependencies.

Run from any directory: python3 scripts/render_header.py
The artwork is intentionally static and contains no embedded images or web fonts.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEMES = {
    "light": {
        "paper": "#F8F4ED",
        "ink": "#1C2934",
        "muted": "#66716F",
        "line": "#DCD7CB",
        "accent": "#B84E42",
        "teal": "#457C76",
        "gold": "#A18650",
        "panel": "#F0ECE3",
        "key": "#FDFBF6",
        "black_key": "#34404A",
    },
    "dark": {
        "paper": "#121B25",
        "ink": "#F3EEE4",
        "muted": "#A5B2B9",
        "line": "#34414C",
        "accent": "#E78272",
        "teal": "#83BBB0",
        "gold": "#CBB079",
        "panel": "#1B2631",
        "key": "#E3DED3",
        "black_key": "#121B25",
    },
}


def render(theme: str) -> str:
    c = THEMES[theme]
    staff = "\n".join(
        f'<path d="M800 {125 + n * 18}H1110"/>' for n in range(5)
    )
    grid = "\n".join(
        f'<circle cx="{x}" cy="{y}" r="1"/>'
        for x in range(788, 1133, 24)
        for y in range(66, 283, 24)
    )
    keys = "\n".join(
        f'<rect x="{836 + n * 18}" y="246" width="17" height="35" '
        f'rx="1.5" fill="{c["key"]}"/>'
        for n in range(14)
    )
    black_keys = "\n".join(
        f'<rect x="{849 + n * 18}" y="246" width="9" height="22" '
        f'rx="1.2" fill="{c["black_key"]}"/>'
        for n in range(13)
        if n % 7 not in (2, 6)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="340" viewBox="0 0 1200 340" role="img" aria-labelledby="title desc">
  <title id="title">Kronecker — Theory, Code, Piano, Poetry</title>
  <desc id="desc">KiriAky107. Theory, code, piano, and poetry. A vermilion-accented personal header combining connected ideas with musical notation.</desc>
  <defs>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{c['accent']}"/>
      <stop offset=".58" stop-color="{c['gold']}"/>
      <stop offset="1" stop-color="{c['teal']}"/>
    </linearGradient>
  </defs>
  <rect x=".5" y=".5" width="1199" height="339" rx="18" fill="{c['paper']}" stroke="{c['line']}"/>
  <path d="M26 1H1174" stroke="url(#edge)" stroke-width="2"/>

  <!-- A quiet editorial masthead, readable at normal README widths. -->
  <g font-family="'Segoe UI', Arial, sans-serif">
    <circle cx="64" cy="62" r="4" fill="{c['accent']}"/>
    <text x="80" y="67" fill="{c['muted']}" font-family="'SFMono-Regular', Consolas, monospace" font-size="16" letter-spacing="1.2">KiriAky107</text>
    <text x="58" y="161" fill="{c['ink']}" font-family="Georgia, 'Times New Roman', serif" font-size="90" letter-spacing="-3">Kronecker<tspan fill="{c['accent']}">.</tspan></text>
    <text x="64" y="208" fill="{c['muted']}" font-size="25" letter-spacing=".5">Theory <tspan fill="{c['accent']}">·</tspan> Code <tspan fill="{c['accent']}">·</tspan> Piano <tspan fill="{c['accent']}">·</tspan> Poetry</text>
    <path d="M64 234H119" stroke="{c['accent']}" stroke-width="2"/>
    <text x="64" y="272" fill="{c['ink']}" font-size="18">Ideas, melodies, and lines of verse.</text>
    <g fill="{c['muted']}" font-family="'SFMono-Regular', Consolas, monospace" font-size="11.5" letter-spacing="1.3">
      <text x="64" y="305">DIALECTICS</text>
      <text x="218" y="305">OPEN SOURCE</text>
      <text x="378" y="305">MUSIC &amp; VERSE</text>
    </g>
    <path d="M198 296V306M358 296V306" stroke="{c['line']}"/>
  </g>

  <!-- One motif: notes become connected knowledge, then an instrument. -->
  <path d="M727 57V283" stroke="{c['line']}"/>
  <g fill="{c['line']}" opacity=".45">{grid}</g>
  <text x="800" y="85" fill="{c['muted']}" font-family="'SFMono-Regular', Consolas, monospace" font-size="11" letter-spacing="1.5">IDEAS IN COUNTERPOINT</text>
  <g stroke="{c['line']}" stroke-width="1" fill="none">{staff}</g>
  <path d="M835 179C857 179 873 143 906 143S952 161 978 161S1021 125 1052 125" fill="none" stroke="{c['teal']}" stroke-width="1.8"/>
  <path d="M835 179C863 213 938 213 978 161M906 143C925 105 1008 95 1052 125" fill="none" stroke="{c['gold']}" stroke-width="1" stroke-dasharray="3 5" opacity=".8"/>
  <g stroke="{c['ink']}" stroke-width="1.7">
    <path d="M843 177V134M914 141V101M986 159V116M1060 123V94"/>
  </g>
  <g fill="{c['paper']}" stroke="{c['teal']}" stroke-width="1.2">
    <circle cx="835" cy="179" r="12"/>
    <circle cx="906" cy="143" r="12"/>
    <circle cx="978" cy="161" r="12"/>
    <circle cx="1052" cy="125" r="12"/>
  </g>
  <g fill="{c['accent']}">
    <ellipse cx="835" cy="179" rx="8.5" ry="5.5" transform="rotate(-23 835 179)"/>
    <ellipse cx="906" cy="143" rx="8.5" ry="5.5" transform="rotate(-23 906 143)"/>
    <ellipse cx="978" cy="161" rx="8.5" ry="5.5" transform="rotate(-23 978 161)"/>
    <ellipse cx="1052" cy="125" rx="8.5" ry="5.5" transform="rotate(-23 1052 125)"/>
  </g>
  <g fill="{c['muted']}" font-family="'SFMono-Regular', Consolas, monospace" font-size="10.5" letter-spacing=".7">
    <text x="816" y="226">notes</text>
    <text x="922" y="226">reason</text>
    <text x="1038" y="226">create</text>
  </g>
  <rect x="832" y="242" width="260" height="43" rx="4" fill="{c['panel']}" stroke="{c['line']}"/>
  {keys}
  {black_keys}
  <text x="1125" y="306" text-anchor="end" fill="{c['muted']}" font-family="'SFMono-Regular', Consolas, monospace" font-size="10.5" letter-spacing="1.1">READ · CREATE · REFLECT</text>
</svg>
'''


def main() -> None:
    output = ROOT / "assets"
    output.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        path = output / f"header-{theme}.svg"
        path.write_text(render(theme), encoding="utf-8")
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
