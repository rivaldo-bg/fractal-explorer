"""
Fractal Explorer — Mandelbrot & Julia Sets
Requirements: pip install numpy pillow
Controls:
  Left-click drag  : pan
  Scroll wheel     : zoom in/out
  Right-click      : set Julia seed from Mandelbrot view
  R                : reset view
  S                : save screenshot (PNG)
  Tab              : switch Mandelbrot ↔ Julia
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
from PIL import Image, ImageTk
import time
import os

# ── Palette ────────────────────────────────────────────────────────────────────
BG        = "#0d0f18"
PANEL_BG  = "#13151f"
ACCENT    = "#00e5ff"
DIM       = "#3a3f55"
TEXT      = "#dde3f5"
WARN      = "#ff4d6d"

MAX_ITER_DEFAULT = 200

def make_palette(n: int) -> np.ndarray:
    """Smooth cyclic palette: deep blue → cyan → gold → deep blue."""
    t = np.linspace(0, 1, n)
    r = (0.5 + 0.5 * np.sin(2 * np.pi * (t + 0.0))) * 255
    g = (0.5 + 0.5 * np.sin(2 * np.pi * (t + 0.33))) * 255
    b = (0.5 + 0.5 * np.sin(2 * np.pi * (t + 0.67))) * 255
    palette = np.stack([r, g, b], axis=1).astype(np.uint8)
    palette[0] = [0, 0, 0]          # inside set → black
    return palette


# ── Core computation ───────────────────────────────────────────────────────────
def compute_fractal(
    width: int, height: int,
    x_min: float, x_max: float,
    y_min: float, y_max: float,
    max_iter: int,
    julia: bool = False,
    c: complex = complex(-0.7, 0.27),
) -> np.ndarray:
    """Return smooth iteration counts as float32 array (0 = inside set)."""
    x = np.linspace(x_min, x_max, width, dtype=np.float64)
    y = np.linspace(y_min, y_max, height, dtype=np.float64)
    C_re, C_im = np.meshgrid(x, y)

    if julia:
        Z_re, Z_im = C_re.copy(), C_im.copy()
        c_re, c_im = c.real, c.imag
    else:
        Z_re = np.zeros_like(C_re)
        Z_im = np.zeros_like(C_im)
        c_re, c_im = C_re, C_im

    count  = np.zeros(Z_re.shape, dtype=np.float32)
    active = np.ones(Z_re.shape,  dtype=bool)

    for i in range(1, max_iter + 1):
        zr2 = Z_re * Z_re
        zi2 = Z_im * Z_im
        mask = active & ((zr2 + zi2) > 4.0)
        # Smooth colouring: fractional escape count
        if mask.any():
            log_z  = np.log(np.sqrt(zr2[mask] + zi2[mask]))
            smooth = i - np.log2(np.maximum(log_z, 1e-10))
            count[mask] = np.clip(smooth, 0, max_iter)
            active[mask] = False
        zr_new        =  Z_re * Z_re - Z_im * Z_im + (c_re if julia else c_re)
        Z_im[active]  = 2 * Z_re[active] * Z_im[active] + (c_im if julia else c_im[active])
        Z_re[active]  = zr_new[active]

    return count   # 0 for points still inside


def count_to_image(count: np.ndarray, palette: np.ndarray, max_iter: int) -> Image.Image:
    norm = (count / max_iter * (len(palette) - 1)).astype(np.int32)
    norm = np.clip(norm, 0, len(palette) - 1)
    rgb  = palette[norm]
    return Image.fromarray(rgb, "RGB")


# ── Main window ────────────────────────────────────────────────────────────────
class FractalExplorer(tk.Tk):
    W, H = 800, 600

    def __init__(self):
        super().__init__()
        self.title("Fractal Explorer")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.julia_mode = False
        self.julia_c    = complex(-0.7, 0.27015)
        self.max_iter   = MAX_ITER_DEFAULT
        self.palette    = make_palette(1024)
        self._drag_start = None
        self._render_job = None
        self._photo      = None

        self._reset_view()
        self._build_ui()
        self._schedule_render()

    # ── View helpers ───────────────────────────────────────────────────────────
    def _reset_view(self):
        if self.julia_mode:
            self.x_min, self.x_max = -2.0,  2.0
            self.y_min, self.y_max = -1.5,  1.5
        else:
            self.x_min, self.x_max = -2.5,  1.0
            self.y_min, self.y_max = -1.25, 1.25

    @property
    def _span_x(self): return self.x_max - self.x_min
    @property
    def _span_y(self): return self.y_max - self.y_min

    def _pixel_to_complex(self, px, py):
        re = self.x_min + px / self.W * self._span_x
        im = self.y_min + py / self.H * self._span_y
        return re, im

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Top panel
        top = tk.Frame(self, bg=PANEL_BG, padx=14, pady=8)
        top.pack(fill="x")

        self._title_var = tk.StringVar(value="MANDELBROT SET")
        tk.Label(top, textvariable=self._title_var,
                 font=("Courier", 13, "bold"), bg=PANEL_BG, fg=ACCENT).pack(side="left")

        right = tk.Frame(top, bg=PANEL_BG)
        right.pack(side="right")

        tk.Button(right, text="⟳ Reset", command=self._on_reset,
                  font=("Courier", 9), bg=DIM, fg=TEXT,
                  activebackground=ACCENT, relief="flat", padx=8).pack(side="left", padx=4)
        tk.Button(right, text="⇄ Switch", command=self._on_switch,
                  font=("Courier", 9), bg=DIM, fg=TEXT,
                  activebackground=ACCENT, relief="flat", padx=8).pack(side="left", padx=4)
        tk.Button(right, text="💾 Save", command=self._on_save,
                  font=("Courier", 9), bg=DIM, fg=TEXT,
                  activebackground=ACCENT, relief="flat", padx=8).pack(side="left", padx=4)

        # Canvas
        self.canvas = tk.Canvas(self, width=self.W, height=self.H,
                                bg="black", cursor="crosshair",
                                highlightthickness=0)
        self.canvas.pack()

        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>",      self._on_scroll)      # Windows/macOS
        self.canvas.bind("<Button-4>",        self._on_scroll)      # Linux scroll up
        self.canvas.bind("<Button-5>",        self._on_scroll)      # Linux scroll down
        self.canvas.bind("<Button-3>",        self._on_right_click)
        self.bind("<KeyPress>", self._on_key)

        # Status bar
        bot = tk.Frame(self, bg=PANEL_BG, padx=14, pady=5)
        bot.pack(fill="x")
        self._status_var = tk.StringVar(value="")
        tk.Label(bot, textvariable=self._status_var,
                 font=("Courier", 8), bg=PANEL_BG, fg=DIM).pack(side="left")

        self._julia_var = tk.StringVar(value="")
        tk.Label(bot, textvariable=self._julia_var,
                 font=("Courier", 8), bg=PANEL_BG, fg=WARN).pack(side="right")

        self.canvas.bind("<Motion>", self._on_mouse_move)

    # ── Rendering ──────────────────────────────────────────────────────────────
    def _schedule_render(self, delay=30):
        if self._render_job:
            self.after_cancel(self._render_job)
        self._render_job = self.after(delay, self._render)

    def _render(self):
        t0 = time.perf_counter()
        count = compute_fractal(
            self.W, self.H,
            self.x_min, self.x_max,
            self.y_min, self.y_max,
            self.max_iter,
            julia=self.julia_mode,
            c=self.julia_c,
        )
        img = count_to_image(count, self.palette, self.max_iter)
        self._photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor="nw", image=self._photo)
        elapsed = time.perf_counter() - t0
        self._status_var.set(
            f"x:[{self.x_min:.4f}, {self.x_max:.4f}]  "
            f"y:[{self.y_min:.4f}, {self.y_max:.4f}]  "
            f"iter:{self.max_iter}  render:{elapsed*1000:.0f}ms"
        )
        if self.julia_mode:
            self._julia_var.set(f"c = {self.julia_c.real:+.5f} {self.julia_c.imag:+.5f}i")

    # ── Interactions ───────────────────────────────────────────────────────────
    def _on_press(self, e):
        self._drag_start = (e.x, e.y, self.x_min, self.x_max,
                            self.y_min, self.y_max)

    def _on_drag(self, e):
        if not self._drag_start:
            return
        px0, py0, xmin0, xmax0, ymin0, ymax0 = self._drag_start
        dx = (px0 - e.x) / self.W * (xmax0 - xmin0)
        dy = (py0 - e.y) / self.H * (ymax0 - ymin0)
        self.x_min, self.x_max = xmin0 + dx, xmax0 + dx
        self.y_min, self.y_max = ymin0 + dy, ymax0 + dy
        self._schedule_render(60)

    def _on_release(self, e):
        self._drag_start = None

    def _on_scroll(self, e):
        # Determine zoom direction
        if e.num == 4 or e.delta > 0:
            factor = 0.8
        else:
            factor = 1.25

        mx, my = self._pixel_to_complex(e.x, e.y)
        self.x_min = mx + (self.x_min - mx) * factor
        self.x_max = mx + (self.x_max - mx) * factor
        self.y_min = my + (self.y_min - my) * factor
        self.y_max = my + (self.y_max - my) * factor
        # Ramp up iterations when zooming in
        if factor < 1:
            self.max_iter = min(2000, int(self.max_iter * 1.08))
        self._schedule_render(80)

    def _on_right_click(self, e):
        """Set Julia seed from current Mandelbrot position."""
        re, im = self._pixel_to_complex(e.x, e.y)
        self.julia_c   = complex(re, im)
        self.julia_mode = True
        self._title_var.set("JULIA SET")
        self._reset_view()
        self._schedule_render()

    def _on_mouse_move(self, e):
        re, im = self._pixel_to_complex(e.x, e.y)
        sign = "+" if im >= 0 else ""
        self._status_var.set(
            f"z = {re:.6f} {sign}{im:.6f}i   "
            f"x:[{self.x_min:.4f}, {self.x_max:.4f}]  "
            f"iter:{self.max_iter}"
        )

    def _on_reset(self):
        self.max_iter = MAX_ITER_DEFAULT
        self._reset_view()
        self._schedule_render()

    def _on_switch(self):
        self.julia_mode = not self.julia_mode
        self._title_var.set("JULIA SET" if self.julia_mode else "MANDELBROT SET")
        self._julia_var.set("" if not self.julia_mode else self._julia_var.get())
        self.max_iter = MAX_ITER_DEFAULT
        self._reset_view()
        self._schedule_render()

    def _on_save(self):
        count = compute_fractal(
            self.W, self.H,
            self.x_min, self.x_max,
            self.y_min, self.y_max,
            self.max_iter,
            julia=self.julia_mode,
            c=self.julia_c,
        )
        img  = count_to_image(count, self.palette, self.max_iter)
        name = f"fractal_{'julia' if self.julia_mode else 'mandelbrot'}_{int(time.time())}.png"
        path = os.path.join(os.path.expanduser("~"), name)
        img.save(path)
        self._status_var.set(f"Saved → {path}")

    def _on_key(self, e):
        key = e.keysym
        if key.lower() == "r":
            self._on_reset()
        elif key == "Tab":
            self._on_switch()
        elif key.lower() == "s":
            self._on_save()
        elif key in ("+", "equal"):
            self.max_iter = min(2000, self.max_iter + 50)
            self._schedule_render()
        elif key == "minus":
            self.max_iter = max(50, self.max_iter - 50)
            self._schedule_render()


if __name__ == "__main__":
    app = FractalExplorer()
    app.mainloop()
