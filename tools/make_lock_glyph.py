#!/usr/bin/env python3
"""Lock-screen art: a ring-gate glyph.

    tools/make_lock_glyph.py

Writes ../unlock.png (1108x523, transparent, drawn in the theme foreground)
and ../preview-unlock.png (1920x1080, the glyph over 3-ring-gate.png).
Needs numpy and Pillow; run make_backgrounds.py first.
"""
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FG = np.array([207, 214, 223]); ORANGE = np.array([232, 117, 42])


def glyph(w, h):
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    cx, cy = w / 2, h / 2; R = 0.42 * h
    r = np.hypot(xx - cx, yy - cy); ang = np.arctan2(yy - cy, xx - cx)
    ring = np.exp(-((r - R) / (0.018 * h)) ** 2)
    ticks = ((np.abs(np.sin(ang * 6)) > 0.97) & (r > R * 0.90) & (r < R * 1.10)).astype(float)
    inner = np.exp(-((r - R * 0.72) / (0.006 * h)) ** 2) * 0.6
    a = np.clip(ring + inner + ticks, 0, 1)
    rgb = np.where(ticks[..., None] > 0, ORANGE, FG)
    return np.dstack([rgb, a * 255]).astype(np.uint8)


def main():
    Image.fromarray(glyph(1108, 523), "RGBA").save(os.path.join(ROOT, "unlock.png"))
    bg = Image.open(os.path.join(ROOT, "backgrounds", "3-ring-gate.png")).convert("RGBA").resize((1920, 1080), Image.LANCZOS)
    g = Image.fromarray(glyph(1108, 523), "RGBA").resize((554, 262), Image.LANCZOS)
    bg.alpha_composite(g, ((1920 - 554) // 2, (1080 - 262) // 2 - 120))
    bg.convert("RGB").save(os.path.join(ROOT, "preview-unlock.png"))
    print("unlock.png, preview-unlock.png")


if __name__ == "__main__":
    main()
