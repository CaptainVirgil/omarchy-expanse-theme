#!/usr/bin/env python3
"""Orthographic renders of a ship model, for sprites and reference views.

    tools/render_ship.py views  MODEL            four rotations around the long axis, side by side
    tools/render_ship.py side   MODEL K [--flip] [--len 576] [--flat]
                                                 one view (K = 0..3 as numbered by `views`),
                                                 saved as RGB + mask arrays and a PNG

Reads .glb/.gltf (with textures, via trimesh) or binary .stl (geometry only).
The long axis is found by PCA, so any model orientation works. A display
stand, if the model has one, is dropped as the connected component that
hangs far below the hull mid-length (see drop_stand). Output goes to
tools/out/. Pure numpy z-buffer rasteriser: a few minutes for 500k faces.

Needs numpy, Pillow and trimesh (`pip install numpy pillow trimesh`).
"""
import argparse
import os
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def load(path):
    """Return vertices (N,3), faces (M,3), per-vertex colours (N,3) in 0..1."""
    if path.lower().endswith(".stl"):
        with open(path, "rb") as h:
            h.read(80)
            n = struct.unpack("<I", h.read(4))[0]
            rec = np.frombuffer(h.read(n * 50), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
        tris = rec["v"].astype(np.float64)
        V = tris.reshape(-1, 3)
        F = np.arange(len(V)).reshape(-1, 3)
        C = np.full((len(V), 3), 0.8)
        return V, F, C
    import trimesh
    sc = trimesh.load(path)
    V, F, C = [], [], []
    off = 0
    for g in (sc.dump(concatenate=False) if isinstance(sc, trimesh.Scene) else [sc]):
        try:
            cols = np.asarray(g.visual.to_color().vertex_colors)[:, :3].astype(float) / 255
        except Exception:
            cols = np.full((len(g.vertices), 3), 0.6)
        V.append(np.asarray(g.vertices, float)); F.append(np.asarray(g.faces) + off); C.append(cols)
        off += len(g.vertices)
    return np.vstack(V), np.vstack(F), np.vstack(C)


def principal_frame(V):
    c = V.mean(0)
    w, E = np.linalg.eigh(np.cov((V - c).T))
    axes = E[:, np.argsort(-w)]          # long axis first
    return (V - c) @ axes


def drop_stand(X, F):
    """Remove connected components that hang far below the hull (display stands)."""
    T = X[F]
    key = np.round(T.reshape(-1, 3), 3)
    uniq, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1, 3)
    parent = np.arange(len(uniq))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b, c in inv:
        ra, rb, rc = find(a), find(b), find(c)
        parent[rb] = ra; parent[rc] = ra
    roots = np.array([find(i) for i in inv[:, 0]])
    L = T[:, :, 0].max() - T[:, :, 0].min()
    keep = np.ones(len(F), bool)
    for axis_sign in (1, -1):           # the stand may be on either side of the long axis plane
        ys = T[:, :, 1] * axis_sign
        ymin, ymax = ys.min(), ys.max()
        for ci in np.unique(roots):
            m = roots == ci
            by0 = ys[m].min(); bx = T[m][:, :, 0]
            if m.sum() > 200 and by0 < ymin + 0.02 * (ymax - ymin) and (bx.max() - bx.min()) < 0.45 * L:
                # only a stand if the rest of the model does not reach that low
                rest = ys[~m].min()
                if by0 < rest - 0.05 * (ymax - ymin):
                    print(f"dropping stand-like component: {m.sum()} faces", file=sys.stderr)
                    keep &= ~m
    return F[keep]


def render(X, F, C, ang, length, flip=False, flat=False):
    ca, sa = np.cos(ang), np.sin(ang)
    R = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]])
    P = X @ R.T
    if flip:
        P[:, 0] *= -1
    T = P[F]
    Cc = np.ones_like(C[F]) if flat else C[F]
    xs, ys, zs = T[:, :, 0], T[:, :, 1], T[:, :, 2]
    x0, x1 = xs.min(), xs.max(); y0, y1 = ys.min(), ys.max()
    sc = length / (x1 - x0)
    Wd = length + 4; Hd = int(np.ceil((y1 - y0) * sc)) + 4
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1), 1e-9)[:, None]
    nrm[nrm[:, 2] < 0] *= -1
    light = np.array([-0.35, 0.55, 0.76]); light /= np.linalg.norm(light)
    shade = 0.35 + 0.65 * np.clip(nrm @ light, 0, 1)
    img = np.zeros((Hd, Wd, 3)); zb = np.full((Hd, Wd), -1e9)
    px = (xs - x0) * sc + 2; py = (y1 - ys) * sc + 2
    for i in np.argsort(zs.mean(1)):
        tx, ty = px[i], py[i]
        xa, xb = max(int(tx.min()), 0), min(int(np.ceil(tx.max())), Wd - 1)
        ya, yb = max(int(ty.min()), 0), min(int(np.ceil(ty.max())), Hd - 1)
        if xb < xa or yb < ya:
            continue
        gx, gy = np.meshgrid(np.arange(xa, xb + 1), np.arange(ya, yb + 1))
        d = (tx[1] - tx[0]) * (ty[2] - ty[0]) - (tx[2] - tx[0]) * (ty[1] - ty[0])
        if abs(d) < 1e-9:
            continue
        l1 = ((tx[1] - gx) * (ty[2] - gy) - (tx[2] - gx) * (ty[1] - gy)) / d
        l2 = ((tx[2] - gx) * (ty[0] - gy) - (tx[0] - gx) * (ty[2] - gy)) / d
        l3 = 1 - l1 - l2
        m = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        if not m.any():
            continue
        z = zs[i].mean(); sel = m & (z > zb[gy, gx])
        if not sel.any():
            continue
        col = (l1[..., None] * Cc[i, 0] + l2[..., None] * Cc[i, 1] + l3[..., None] * Cc[i, 2]) * shade[i]
        zb[gy[sel], gx[sel]] = z; img[gy[sel], gx[sel]] = col[sel]
    return np.clip(img, 0, 1), zb > -1e8


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["views", "side"])
    ap.add_argument("model")
    ap.add_argument("k", nargs="?", type=int, default=0, help="rotation index 0..3 for `side`")
    ap.add_argument("--flip", action="store_true", help="mirror so the bow points the other way")
    ap.add_argument("--len", type=int, default=576, help="rendered length in px (side)")
    ap.add_argument("--flat", action="store_true", help="ignore textures, shading only")
    ap.add_argument("--keep-stand", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    V, F, C = load(a.model)
    X = principal_frame(V)
    if not a.keep_stand:
        F = drop_stand(X, F)
    print(f"{len(F)} faces", file=sys.stderr)
    if a.mode == "views":
        ims = []
        for k in range(4):
            img, mask = render(X, F, C, k * np.pi / 2, 720)
            arr = (img * 255).astype(np.uint8); arr[~mask] = (30, 30, 36)
            ims.append(Image.fromarray(arr)); print("view", k, arr.shape, file=sys.stderr)
        W = max(i.width for i in ims); H = sum(i.height for i in ims) + 30
        out = Image.new("RGB", (W, H), (60, 60, 70)); y = 0
        for i in ims:
            out.paste(i, (0, y)); y += i.height + 10
        out.save(os.path.join(OUT, "views.png")); print(os.path.join(OUT, "views.png"))
    else:
        img, mask = render(X, F, C, a.k * np.pi / 2, a.len, a.flip, a.flat)
        tag = "_flat" if a.flat else ""
        np.save(os.path.join(OUT, f"side{tag}_rgb.npy"), img); np.save(os.path.join(OUT, "side_mask.npy"), mask)
        arr = (img * 255).astype(np.uint8)
        Image.fromarray(np.dstack([arr, (mask * 255).astype(np.uint8)]), "RGBA").save(os.path.join(OUT, f"side{tag}.png"))
        print(os.path.join(OUT, f"side{tag}.png"))


if __name__ == "__main__":
    main()
