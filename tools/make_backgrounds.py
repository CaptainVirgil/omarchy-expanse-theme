#!/usr/bin/env python3
"""Generate the theme's wallpapers procedurally (no third-party imagery).

    tools/make_backgrounds.py [--size 3840x2160] [--out backgrounds]

Three images, all seeded so re-runs are identical:
  1-deep-space.png   two-layer star field with a faint orange/blue nebula
  2-drive-plume.png  the same sky with an Epstein-drive streak crossing it
  3-ring-gate.png    a ring gate: thin bright annulus with a soft glow

Needs numpy and Pillow.
"""
import argparse
import os

import numpy as np
from PIL import Image, ImageFilter

BG = np.array([10, 14, 20]) / 255
ORANGE = np.array([232, 117, 42]) / 255
BLUE = np.array([79, 143, 224]) / 255
TEAL = np.array([79, 182, 198]) / 255
FG = np.array([207, 214, 223]) / 255


def noise(w, h, rng, octaves=(640, 320, 160, 80), weights=(0.55, 0.25, 0.13, 0.07)):
    """Smooth value noise: blurred random grids summed over a few large scales."""
    acc = np.zeros((h, w))
    for cell, wt in zip(octaves, weights):
        gw, gh = w // cell + 3, h // cell + 3
        g = rng.random((gh, gw))
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        im = im.filter(ImageFilter.GaussianBlur(cell / 6))
        acc += wt * np.asarray(im, dtype=float) / 255
    return acc / sum(weights)


def stars(w, h, rng, n, bright, size_px):
    layer = np.zeros((h, w))
    xs = rng.integers(0, w, n); ys = rng.integers(0, h, n)
    mag = rng.random(n) ** 3 * bright
    layer[ys, xs] = mag
    im = Image.fromarray((np.clip(layer, 0, 1) * 255).astype(np.uint8))
    im = im.filter(ImageFilter.GaussianBlur(size_px))
    return np.asarray(im, dtype=float) / 255 * 3.0


def sky(w, h, rng):
    base = np.ones((h, w, 3)) * BG
    neb = noise(w, h, rng)
    neb = np.clip((neb - 0.40) * 2.4, 0, 1) ** 1.4
    # orange at the lower left, blue toward the upper right
    gx = np.linspace(0, 1, w)[None, :]; gy = np.linspace(1, 0, h)[:, None]
    mix = np.clip(0.5 * gx + 0.5 * gy, 0, 1)
    tint = ORANGE * (1 - mix)[..., None] + BLUE * mix[..., None]
    base += neb[..., None] * tint * 0.28
    base += (stars(w, h, rng, w * h // 700, 1.0, 0.7))[..., None] * FG * 1.2   # far, tiny
    base += (stars(w, h, rng, w * h // 6000, 1.0, 1.3))[..., None] * FG * 1.4  # near, soft
    big = stars(w, h, rng, w * h // 90000, 1.0, 2.6)
    base += big[..., None] * (FG * 0.6 + TEAL * 0.4) * 1.5
    return base


def to_image(arr):
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))


def drive_plume(arr, w, h):
    """A thin diagonal streak, blue core, white centre, fading tail."""
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    x0, y0 = 0.15 * w, 0.72 * h        # tail
    x1, y1 = 0.78 * w, 0.30 * h        # head (the ship, off-frame small)
    dx, dy = x1 - x0, y1 - y0; L = np.hypot(dx, dy)
    t = ((xx - x0) * dx + (yy - y0) * dy) / (L * L)
    d = np.abs((xx - x0) * dy - (yy - y0) * dx) / L
    along = np.clip(t, 0, 1)
    width = 2.0 + 26.0 * (1 - along) ** 1.5
    core = np.exp(-(d / width) ** 2) * (along ** 0.8) * (t > 0) * (t < 1.02)
    glow = np.exp(-(d / (width * 6)) ** 2) * (along ** 0.8) * (t > 0) * (t < 1.02) * 0.35
    out = arr.copy()
    out += glow[..., None] * BLUE
    out += core[..., None] * (BLUE * 0.4 + np.array([1, 1, 1]) * 0.6)
    return out


def ring_gate(arr, w, h):
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    cx, cy = 0.62 * w, 0.52 * h; R = 0.30 * h
    r = np.hypot(xx - cx, yy - cy)
    ring = np.exp(-((r - R) / (0.012 * h)) ** 2)
    glow = np.exp(-((r - R) / (0.09 * h)) ** 2) * 0.35
    inner = np.clip(1 - r / R, 0, 1) ** 2 * 0.10       # faint disc inside the gate
    out = arr.copy()
    out += glow[..., None] * TEAL
    out += ring[..., None] * (TEAL * 0.3 + FG * 0.7)
    out += inner[..., None] * BLUE
    # spokes: 12 short radial marks on the ring
    ang = np.arctan2(yy - cy, xx - cx)
    spokes = (np.abs(np.sin(ang * 6)) > 0.985) & (r > R * 0.96) & (r < R * 1.06)
    out[spokes] = out[spokes] * 0.3 + ORANGE * 0.7
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="3840x2160")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backgrounds"))
    a = ap.parse_args()
    w, h = (int(v) for v in a.size.split("x"))
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(2350)     # the Roci's hull number, roughly
    base = sky(w, h, rng)
    to_image(base).save(os.path.join(a.out, "1-deep-space.png"), optimize=True)
    to_image(drive_plume(base, w, h)).save(os.path.join(a.out, "2-drive-plume.png"), optimize=True)
    to_image(ring_gate(base, w, h)).save(os.path.join(a.out, "3-ring-gate.png"), optimize=True)
    print("wrote 3 backgrounds to", os.path.abspath(a.out))


if __name__ == "__main__":
    main()
