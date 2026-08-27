#!/usr/bin/env python3
"""Precompute 36 frames of the classic spinning ASCII donut and write assets/donut.svg.

Usage:
    python scripts/gen_donut.py
"""

from __future__ import annotations

import math
from pathlib import Path

# Output ~44 cols x 22 rows. 36 frames = one full turn of A and B (seamless loop).
COLS = 44
ROWS = 22
N_FRAMES = 36
CHARS = ".,-~:;=!*#$@"

# Torus radii and projection (a1k0n / donut.c)
R1 = 1.0
R2 = 2.0
K2 = 5.0
# K1 chosen so the projected torus fills most of the 44x22 field.
K1 = COLS * K2 * 3.0 / (8.0 * (R1 + R2))
# Courier 14px / 16px line-height ≈ 8.4/16; compensate so the donut looks round.
ASPECT = 8.4 / 16.0

THETA_STEP = 0.07
PHI_STEP = 0.02

OUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "donut.svg"

SVG_W = 900
SVG_H = 420
FONT_SIZE = 14
LINE_H = 16
# Courier New 14px advance ≈ 8.4px
CHAR_W = 8.4
TEXT_X = round((SVG_W - COLS * CHAR_W) / 2, 1)
TEXT_Y0 = 42


def render_frame(A: float, B: float) -> list[str]:
    """Project a torus at rotation (A, B) into a COLS x ROWS ASCII buffer."""
    output = [[" "] * COLS for _ in range(ROWS)]
    zbuffer = [[0.0] * COLS for _ in range(ROWS)]

    cosA, sinA = math.cos(A), math.sin(A)
    cosB, sinB = math.cos(B), math.sin(B)

    theta = 0.0
    while theta < math.tau:
        costheta, sintheta = math.cos(theta), math.sin(theta)
        phi = 0.0
        while phi < math.tau:
            cosphi, sinphi = math.cos(phi), math.sin(phi)

            circlex = R2 + R1 * costheta
            circley = R1 * sintheta

            x = circlex * (cosB * cosphi + sinA * sinB * sinphi) - circley * cosA * sinB
            y = circlex * (sinB * cosphi - sinA * cosB * sinphi) + circley * cosA * cosB
            z = K2 + cosA * circlex * sinphi + circley * sinA
            ooz = 1.0 / z

            xp = int(COLS / 2 + K1 * ooz * x)
            yp = int(ROWS / 2 - K1 * ASPECT * ooz * y)

            # Surface luminance (donut.c). Only draw front-facing samples.
            L = (
                cosphi * costheta * sinB
                - cosA * costheta * sinphi
                - sinA * sintheta
                + cosB * (cosA * sintheta - costheta * sinA * sinphi)
            )
            if L > 0 and 0 <= xp < COLS and 0 <= yp < ROWS and ooz > zbuffer[yp][xp]:
                zbuffer[yp][xp] = ooz
                output[yp][xp] = CHARS[min(int(L * 8), 11)]
            phi += PHI_STEP
        theta += THETA_STEP

    return ["".join(row).rstrip() for row in output]


def xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def frame_group(index: int, lines: list[str]) -> str:
    delay = f"{index * 0.1:.1f}s"
    parts = [f'<g class="f" style="animation-delay:{delay}">']
    for i, line in enumerate(lines):
        if not line:
            continue
        y = TEXT_Y0 + i * LINE_H
        parts.append(
            f'<text x="{TEXT_X}" y="{y}" xml:space="preserve">{xml_escape(line)}</text>'
        )
    parts.append("</g>")
    return "\n".join(parts)


def build_svg(frames: list[list[str]]) -> str:
    groups = "\n".join(frame_group(i, lines) for i, lines in enumerate(frames))
    # 1/36 ≈ 2.777…%; hard cut (no cross-fade). 3.6s / 36 = 0.1s per frame.
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_W} {SVG_H}" width="{SVG_W}" height="{SVG_H}" role="img" aria-label="spinning ASCII donut">
  <title>./donut --spin</title>
  <defs>
    <radialGradient id="donutBg" cx="50%" cy="42%" r="70%">
      <stop offset="0%" stop-color="#0d1a0d"/>
      <stop offset="100%" stop-color="#0a0e0a"/>
    </radialGradient>
    <radialGradient id="donutVig" cx="50%" cy="50%" r="72%">
      <stop offset="0%" stop-color="#000000" stop-opacity="0"/>
      <stop offset="65%" stop-color="#000000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.4"/>
    </radialGradient>
    <pattern id="donutScan" width="900" height="2" patternUnits="userSpaceOnUse">
      <rect width="900" height="1" fill="transparent"/>
      <rect y="1" width="900" height="1" fill="rgba(0,0,0,0.25)"/>
    </pattern>
    <linearGradient id="donutBand" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ccffdd" stop-opacity="0"/>
      <stop offset="50%" stop-color="#ccffdd" stop-opacity="0.04"/>
      <stop offset="100%" stop-color="#ccffdd" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="donutClip">
      <rect x="16" y="16" width="868" height="388" rx="12"/>
    </clipPath>
    <style type="text/css"><![CDATA[
    @keyframes frame {{
      0%, 2.777% {{ opacity: 1; }}
      2.778%, 100% {{ opacity: 0; }}
    }}
    @keyframes scanmove {{
      from {{ transform: translateY(-60px); }}
      to {{ transform: translateY(420px); }}
    }}
    @keyframes flicker {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.96; }}
    }}
    .f {{
      opacity: 0;
      animation: frame 3.6s steps(1) infinite;
    }}
    .f text {{
      font-family: 'Courier New', Courier, monospace;
      font-size: {FONT_SIZE}px;
      fill: #33ff66;
      filter: drop-shadow(0 0 4px rgba(51, 255, 102, 0.6));
    }}
    .flicker {{
      animation: flicker 0.15s steps(2) infinite;
    }}
    .scanband {{
      animation: scanmove 6s linear infinite;
      transform-box: fill-box;
      transform-origin: 0 0;
    }}
    ]]></style>
  </defs>

  <rect x="4" y="4" width="892" height="412" rx="18" fill="#0a0e0a" stroke="#1a1a1a" stroke-width="10"/>
  <g clip-path="url(#donutClip)">
    <rect x="16" y="16" width="868" height="388" rx="12" fill="url(#donutBg)"/>
    <g class="flicker">
{groups}
    </g>
    <rect x="16" y="16" width="868" height="388" fill="url(#donutScan)"/>
    <rect class="scanband" x="16" y="16" width="868" height="60" fill="url(#donutBand)"/>
    <rect x="16" y="16" width="868" height="388" fill="url(#donutVig)"/>
  </g>
</svg>
"""


def main() -> None:
    frames = []
    # Offset so frame 0 already shows the torus hole (A=0,B=0 is edge-on).
    # A and B each complete an integer number of turns in 36 frames (seamless).
    a0 = math.pi / 2
    b0 = 0.4
    for i in range(N_FRAMES):
        A = a0 + i * math.tau / N_FRAMES
        B = b0 + i * math.tau / N_FRAMES
        frames.append(render_frame(A, B))

    svg = build_svg(frames)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(svg, encoding="utf-8", newline="\n")
    size = OUT_PATH.stat().st_size
    print(f"wrote {OUT_PATH} ({size} bytes, {N_FRAMES} frames)")
    if size > 200_000:
        raise SystemExit(f"SVG too large ({size} bytes); compress whitespace")


if __name__ == "__main__":
    main()
