# 🔬 Fractal Explorer

> Interactive Mandelbrot & Julia set explorer in Python — pan, zoom, and export fractals with no setup beyond two packages.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Dependencies](https://img.shields.io/badge/Dependencies-numpy%20%7C%20pillow-orange)

---

## Preview

Explore the infinite complexity of the Mandelbrot set, then right-click any point on its boundary to instantly generate the corresponding Julia set.

---

## Features

- 🖱️ **Pan & zoom** — smooth navigation with mouse drag and scroll wheel
- 🌀 **Julia set generator** — right-click any point on the Mandelbrot view to spawn its Julia set
- 🎨 **Smooth colouring** — fractional escape count (logarithmic renormalisation) for seamless colour gradients
- 💾 **PNG export** — save high-quality renders directly from the UI
- ⚡ **NumPy-accelerated** — vectorised computation for fast rendering

---

## Installation

**Requirements:** Python 3.8+

```bash
# Clone the repo
git clone https://github.com/your-username/fractal-explorer.git
cd fractal-explorer

# Install dependencies
pip install numpy pillow
```

---

## Usage

```bash
python fractal_explorer.py
```

### Controls

| Action | Effect |
|---|---|
| Scroll wheel | Zoom in / out (centered on cursor) |
| Left-click drag | Pan |
| Right-click *(Mandelbrot view)* | Spawn Julia set from that complex point |
| `Tab` / ⇄ Switch button | Toggle Mandelbrot ↔ Julia |
| `R` / ⟳ Reset button | Reset view to default |
| `+` / `-` | Increase / decrease max iterations |
| `S` / 💾 Save button | Export current view as PNG |

---

## How It Works

### Mandelbrot Set
The Mandelbrot set is the set of complex numbers *c* for which the iteration:

```
z₀ = 0
zₙ₊₁ = zₙ² + c
```

remains bounded (does not diverge to infinity). Points inside the set are coloured black; points outside are coloured by how quickly they escape.

### Julia Sets
For a Julia set, the same iteration is used, but *c* is **fixed** and the starting value *z₀* varies across every pixel. Right-clicking a point on the Mandelbrot view picks that point as *c*, revealing the unique Julia set it corresponds to.

### Smooth Colouring
Rather than colouring by raw iteration count (which produces harsh bands), the explorer uses the **fractional escape count**:

```
smooth = n - log₂(log(|z|))
```

This produces seamless colour gradients regardless of zoom level.

---

## Project Structure

```
fractal-explorer/
│
├── fractal_explorer.py   # Main application
└── README.md
```

---

## Dependencies

| Package | Purpose |
|---|---|
| [`numpy`](https://numpy.org/) | Vectorised fractal computation |
| [`pillow`](https://python-pillow.org/) | Image rendering and PNG export |
| `tkinter` | GUI window (ships with Python) |

---

## License

MIT — feel free to use, modify, and share.
