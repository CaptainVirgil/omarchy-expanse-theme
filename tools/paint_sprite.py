#!/usr/bin/env python3
"""Turn tools/out/side*.npy from render_ship.py into a small painted sprite.

    tools/paint_sprite.py [--len 150] [--scheme grey|texture] [--out sprite.png]

grey     gunmetal hull from the flat shading, light panels, red markings
         (needs a --flat render; a textured render, if present, nudges the
         grey where the model's own orange panels are)
texture  the model's own paint with the blacks lifted so it reads on a dark
         background

Also writes <out>_big.png (6x, on the theme background) for checking.
"""
import argparse
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
BG = (10, 14, 20)


def resize(arr, size):
    return np.asarray(Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8)).resize(size, Image.LANCZOS)).astype(float) / 255


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--len", type=int, default=150)
    ap.add_argument("--scheme", choices=["grey", "texture"], default="grey")
    ap.add_argument("--out", default=os.path.join(OUT, "sprite.png"))
    a = ap.parse_args()
    mask = np.load(os.path.join(OUT, "side_mask.npy"))
    H4, W4 = mask.shape; W = a.len; H = int(round(H4 * W / W4))
    al = resize(mask.astype(float), (W, H))
    if a.scheme == "texture":
        rgb = resize(np.load(os.path.join(OUT, "side_rgb.npy")), (W, H)).reshape(H, W, 3)
        rgb = np.clip(rgb ** 0.7 * 1.35 + 0.10, 0, 1) * 255
    else:
        flat = np.load(os.path.join(OUT, "side_flat_rgb.npy"))[..., 0]
        s = resize(flat, (W, H))
        dark = np.array([46, 50, 60]); light = np.array([190, 195, 204])
        t = np.clip((s - 0.55) / 0.40, 0, 1) ** 1.5
        rgb = dark * (1 - t)[..., None] + light * t[..., None]
        tex_path = os.path.join(OUT, "side_rgb.npy")
        if os.path.exists(tex_path):
            tex = resize(np.load(tex_path), (W, H)).reshape(H, W, 3)
            orange = (tex[..., 0] > tex[..., 2] * 1.6) & (tex[..., 0] > 0.15)
            rgb[orange] = np.clip(rgb[orange] * 0.9 + 28, 0, 255)
        red = np.array([206, 44, 46])
        xs = np.arange(W)[None, :] / W; ys = np.arange(H)[:, None] / H
        paint = np.zeros((H, W), bool)
        paint |= (xs > 0.28) & (xs < 0.58) & (ys > 0.36) & (ys < 0.42)
        paint |= (xs > 0.28) & (xs < 0.58) & (ys > 0.60) & (ys < 0.64)
        paint |= (xs > 0.74) & (xs < 0.88) & (ys > 0.30) & (ys < 0.44)
        paint |= (xs > 0.14) & (xs < 0.24) & (ys > 0.50) & (ys < 0.56)
        paint &= (al > 0.5) & (s > 0.25)
        rgb[paint] = red * 0.8 + rgb[paint] * 0.2
        for x, y in [(int(W * 0.80), int(H * 0.50)), (int(W * 0.81), int(H * 0.50)), (int(W * 0.47), int(H * 0.52)), (int(W * 0.66), int(H * 0.52))]:
            if al[y, x] > 0.5:
                rgb[y, x] = [235, 240, 255]
    im = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), al * 255]).astype(np.uint8), "RGBA")
    im.save(a.out)
    big = im.resize((W * 6, H * 6), Image.NEAREST)
    bg = Image.new("RGBA", big.size, BG + (255,)); bg.alpha_composite(big)
    bg.convert("RGB").save(a.out.replace(".png", "_big.png"))
    print(a.out, im.size)


if __name__ == "__main__":
    main()
