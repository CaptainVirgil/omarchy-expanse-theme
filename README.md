# Expanse — an Omarchy theme

Deep space, MCRN orange, Epstein-drive blue, hazard red, Belter teal.
A dark theme for [Omarchy](https://omarchy.org) inspired by *The Expanse*.

## Install

```
omarchy theme install https://github.com/CaptainVirgil/omarchy-expanse-theme
```

That clones the repo into `~/.config/omarchy/themes/expanse` and applies it.
Later: `omarchy theme set expanse`, `omarchy theme bg next`, `omarchy theme update`.

## What is in the box

| File | Purpose |
|---|---|
| `colors.toml` | the palette; Omarchy renders every app config from it |
| `backgrounds/` | three procedurally generated 4K wallpapers: deep space, a drive plume crossing it, a ring gate |
| `unlock.png`, `preview-unlock.png` | lock-screen glyph (a ring gate) and its preview |
| `icons.theme` | `Yaru-wartybrown` |
| `keyboard.rgb` | MCRN orange for RGB keyboards |
| `shell.lock.toml` | lock screen field colours |
| `tools/` | the scripts that made the assets (see below) |

## Palette

| role | hex | | role | hex |
|---|---|---|---|---|
| background | `#0a0e14` | | accent / orange | `#e8752a` |
| foreground | `#cfd6df` | | blue | `#4f8fe0` |
| red | `#d63a3f` | | cyan | `#4fb6c6` |
| yellow | `#f0b64a` | | green | `#7fb86b` |
| magenta | `#b57ad9` | | brown | `#7a4e3a` |

Active window border: orange to blue, 45°.

## Tools

Everything visual here is generated, nothing is downloaded art.

- `tools/make_backgrounds.py` renders the three wallpapers from seeded noise
  and star fields. `--size WxH` for other resolutions.
- `tools/make_lock_glyph.py` draws the ring-gate glyph and the lock preview.
- `tools/render_ship.py` renders orthographic views of a ship model
  (`.glb` with textures, or binary `.stl`), finds the long axis by PCA and
  drops a display stand if the model has one. Used to trace a Rocinante
  sprite for a Touch Bar idle animation; kept here because it is the
  reproducible part of that work.
- `tools/paint_sprite.py` turns a rendered side view into a small painted
  sprite (gunmetal with red markings, or the model's own texture).

The ship models are not included; they are third-party assets without a
clear licence. `tools/models/SOURCES.txt` says which files the scripts expect.

```
python -m venv tools/venv && tools/venv/bin/pip install numpy pillow trimesh
tools/venv/bin/python tools/render_ship.py views tools/models/your-ship.glb
tools/venv/bin/python tools/render_ship.py side  tools/models/your-ship.glb 1 --flip --flat
tools/venv/bin/python tools/paint_sprite.py --scheme grey
```

## Licence

MIT for everything in this repository. *The Expanse* and its ships belong to
their rights holders; this is a fan colour scheme.
