"""
utils/colors.py

Color palette, theme constants, and color-manipulation helpers for llamagraph.
No Tkinter or Matplotlib imports — pure Python math.
"""

import colorsys
import math

# ── Dark-mode color palette ──────────────────────────────────────────────────
COLORS: dict[str, str] = {
    'bg':             '#1e1e1e',
    'fg':             '#d4d4d4',
    'accent':         '#0078d4',
    'pp':             '#4ec9b0',   # PP series base color (teal)
    'tg':             '#ce9178',   # TG series base color (orange)
    'checkbox_active': '#2d2d2d',
    'sidebar_bg':     '#252526',
    'panel_bg':       '#2d2d2d',
    'separator':      '#444444',
    'highlight':      '#37373d',
}

DEFAULT_PP_COLOR: str = COLORS['pp']
DEFAULT_TG_COLOR: str = COLORS['tg']

# ── Color math ────────────────────────────────────────────────────────────────

def get_variant_color(base_hex: str, idx: int, angle_deg: int = 28) -> str:
    """
    Rotate the hue of *base_hex* by idx * angle_deg degrees.
    Returns a new hex color string.  Preserves lightness and saturation.
    """
    r = int(base_hex[1:3], 16) / 255.0
    g = int(base_hex[3:5], 16) / 255.0
    b = int(base_hex[5:7], 16) / 255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    h = (h + (idx * angle_deg) / 360.0) % 1.0
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return f'#{int(r2 * 255):02x}{int(g2 * 255):02x}{int(b2 * 255):02x}'


# ── Statistical helpers ───────────────────────────────────────────────────────

def combine_measurements(
    means: list[float], errors: list[float]
) -> tuple[float, float]:
    """
    Combine several mean/error pairs into one unified mean/error.
    Uses simple average for the mean and quadratic combination for errors.
    """
    if not means:
        return (None, None)
    n = len(means)
    mean_unified = sum(means) / n
    err_unified = math.sqrt(sum(e ** 2 for e in errors)) / n
    return mean_unified, err_unified


def normalize_series(
    y_vals: list[float | None],
    y_errs: list[float | None],
    scale_to_pct: bool,
) -> tuple[list[float | None], list[float | None], float]:
    """
    Normalize values and their errors to [0, 1] (or [0, 100] when
    *scale_to_pct* is True).

    Returns (normalized_y, normalized_err, original_max).
    None entries are preserved as None.
    """
    valid = [v for v in y_vals if v is not None]
    if not valid:
        return y_vals, y_errs, 1.0

    max_val = max(valid)
    if max_val == 0:
        return y_vals, y_errs, 1.0

    factor = 100.0 if scale_to_pct else 1.0
    norm_y = [None if v is None else (v / max_val) * factor for v in y_vals]
    norm_e = [None if e is None else (e / max_val) * factor for e in y_errs]
    return norm_y, norm_e, max_val