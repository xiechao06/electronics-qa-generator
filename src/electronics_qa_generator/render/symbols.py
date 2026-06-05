"""IEEE-style circuit symbol drawing functions.

Each function draws a single component symbol on a matplotlib ``Axes`` at position
``(x, y)``, oriented by ``angle`` (degrees, 0 = horizontal left→right).
All position units are in data coordinates (points).
"""

from __future__ import annotations

import math

import matplotlib.patches as mpatches
from matplotlib.axes import Axes

# ---------------------------------------------------------------------------
# Sizing constants (in data-coordinate units ~ "points")
# ---------------------------------------------------------------------------

SYMBOL_LENGTH = 60.0  # main span of a component symbol
LEAD_LENGTH = 20.0  # wire lead length on each side
SYMBOL_HEIGHT = 24.0  # visual height of symbol features
FONT_SIZE_LABEL = 10  # component label font size
FONT_SIZE_NODE = 8  # node label font size
LINE_WIDTH = 1.5  # stroke width for lines

# ---------------------------------------------------------------------------
# Helper: rotate a vector
# ---------------------------------------------------------------------------


def _rot(dx: float, dy: float, angle_deg: float) -> tuple[float, float]:
    """Rotate (dx, dy) by angle_deg degrees counter-clockwise."""
    rad = math.radians(angle_deg)
    c, s = math.cos(rad), math.sin(rad)
    return dx * c - dy * s, dx * s + dy * c


# ---------------------------------------------------------------------------
# Resistor - zigzag
# ---------------------------------------------------------------------------


def draw_resistor(ax: Axes, x: float, y: float, angle: float = 0) -> None:
    """Draw a resistor as a zigzag line."""
    n_zig = 4
    seg_len = SYMBOL_LENGTH / (2 * n_zig)
    points: list[tuple[float, float]] = []
    dx, dy = _rot(seg_len, 0, angle)
    points.append((x, y))
    for i in range(n_zig):
        mid_x = x + dx * (2 * i + 1)
        mid_y = y + dy * (2 * i + 1)
        zig_dx, zig_dy = _rot(0, SYMBOL_HEIGHT / 2 * (1 if i % 2 == 0 else -1), angle)
        points.append((mid_x + zig_dx, mid_y + zig_dy))
    end_x, end_y = _rot(SYMBOL_LENGTH, 0, angle)
    points.append((x + end_x, y + end_y))
    _draw_polyline(ax, points)


# ---------------------------------------------------------------------------
# Capacitor - two parallel plates
# ---------------------------------------------------------------------------


def draw_capacitor(ax: Axes, x: float, y: float, angle: float = 0) -> None:
    """Draw a capacitor as two parallel lines (plates)."""
    gap = 8.0
    half_h = SYMBOL_HEIGHT / 2
    # Plate 1 (left)
    px1, py1 = x, y - half_h
    px2, py2 = x, y + half_h
    # Plate 2 (right)
    gx, gy = _rot(gap, 0, angle)
    qx1, qy1 = x + gx, y - half_h
    qx2, qy2 = x + gx, y + half_h
    ax.plot([px1, px2], [py1, py2], "k-", lw=LINE_WIDTH)
    ax.plot([qx1, qx2], [qy1, qy2], "k-", lw=LINE_WIDTH)
    # Leads
    lead_dx, lead_dy = _rot(-LEAD_LENGTH, 0, angle)
    ax.plot([x + lead_dx, x], [y + lead_dy, y], "k-", lw=LINE_WIDTH)
    end_x, end_y = x + gx, y
    lead2_dx, lead2_dy = _rot(LEAD_LENGTH, 0, angle)
    ax.plot([end_x, end_x + lead2_dx], [end_y, end_y + lead2_dy], "k-", lw=LINE_WIDTH)


# ---------------------------------------------------------------------------
# Inductor - coil (semicircles)
# ---------------------------------------------------------------------------


def draw_inductor(ax: Axes, x: float, y: float, angle: float = 0) -> None:
    """Draw an inductor as a series of semicircular arcs (coil)."""
    n_loops = 3
    seg_len = SYMBOL_LENGTH / (2 * n_loops)
    # Draw as connected semicircles
    for i in range(n_loops):
        cx, cy = _rot(x + seg_len * (2 * i + 1), y, 0)  # center in unrotated space
        # Actually, we need to handle rotation of the arcs properly.
        # For simplicity, draw arcs as line approximations.
        pass
    # Simplified: draw as a bumpy line approximation
    points: list[tuple[float, float]] = []
    n_pts = 24
    for i in range(n_pts):
        t = i / (n_pts - 1)
        px = x + t * SYMBOL_LENGTH
        py = y + math.sin(t * n_loops * 2 * math.pi) * SYMBOL_HEIGHT / 2
        rpx, rpy = _rot(px - x, py - y, angle)
        points.append((x + rpx, y + rpy))
    _draw_polyline(ax, points)


# ---------------------------------------------------------------------------
# Diode - triangle + bar
# ---------------------------------------------------------------------------


def draw_diode(ax: Axes, x: float, y: float, angle: float = 0) -> None:
    """Draw a diode: triangle pointing right → then a vertical bar."""
    # Triangle from (x, y) to (x+SYMBOL_LENGTH-bar_w, y±SYMBOL_HEIGHT/2)
    bar_w = 6.0
    tri_len = SYMBOL_LENGTH - bar_w
    half_h = SYMBOL_HEIGHT / 2

    tri_pts = [
        (x, y),
        _rot_offset(x, y, tri_len, half_h, angle),
        _rot_offset(x, y, tri_len, -half_h, angle),
    ]
    poly = mpatches.Polygon(tri_pts, closed=True, fill=False, edgecolor="black", lw=LINE_WIDTH)
    ax.add_patch(poly)

    # Bar
    bx, by = _rot(tri_len, 0, angle)
    bar_cx, bar_cy = x + bx, y + by
    b1x, b1y = _rot(0, -half_h - 2, angle)
    b2x, b2y = _rot(0, half_h + 2, angle)
    ax.plot(
        [bar_cx + b1x, bar_cx + b2x],
        [bar_cy + b1y, bar_cy + b2y],
        "k-",
        lw=LINE_WIDTH,
    )

    # Leads
    lead_dx, lead_dy = _rot(-LEAD_LENGTH, 0, angle)
    ax.plot([x + lead_dx, x], [y + lead_dy, y], "k-", lw=LINE_WIDTH)
    end_dx, end_dy = _rot(SYMBOL_LENGTH + LEAD_LENGTH, 0, angle)
    ax.plot([x + bx, x + end_dx], [y + by, y + end_dy], "k-", lw=LINE_WIDTH)


def _rot_offset(x: float, y: float, dx: float, dy: float, angle: float) -> tuple[float, float]:
    """Return (x + rotated_dx, y + rotated_dy)."""
    rx, ry = _rot(dx, dy, angle)
    return x + rx, y + ry


# ---------------------------------------------------------------------------
# Voltage source - circle with +/-
# ---------------------------------------------------------------------------


def draw_voltage_source(ax: Axes, x: float, y: float, angle: float = 0) -> None:
    """Draw a voltage source as a circle with + and - signs.
    
    Leads rotate with ``angle`` so that when ``angle=90`` the top lead
    exits upward and the bottom lead downward, matching the connecting
    wire layout in the schematic renderer.
    """
    r = SYMBOL_HEIGHT / 2
    circ = mpatches.Circle((x, y), r, fill=False, edgecolor="black", lw=LINE_WIDTH)
    ax.add_patch(circ)
    # + and - signs inside
    fs = FONT_SIZE_LABEL
    ax.text(x, y + r * 0.35, "+", ha="center", va="center", fontsize=fs, fontweight="bold")
    ax.text(x, y - r * 0.35, "\u2212", ha="center", va="center", fontsize=fs, fontweight="bold")
    # Leads — rotate both the direction and the connection point on the circle
    lead1_start_dx, lead1_start_dy = _rot(-LEAD_LENGTH, 0, angle)
    lead1_end_dx, lead1_end_dy = _rot(-r, 0, angle)  # left side → rotated
    ax.plot(
        [x + lead1_start_dx, x + lead1_end_dx],
        [y + lead1_start_dy, y + lead1_end_dy],
        "k-", lw=LINE_WIDTH,
    )
    lead2_start_dx, lead2_start_dy = _rot(r, 0, angle)  # right side → rotated
    lead2_end_dx, lead2_end_dy = _rot(LEAD_LENGTH, 0, angle)
    ax.plot(
        [x + lead2_start_dx, x + lead2_end_dx],
        [y + lead2_start_dy, y + lead2_end_dy],
        "k-", lw=LINE_WIDTH,
    )


# ---------------------------------------------------------------------------
# Ground - three descending horizontal lines
# ---------------------------------------------------------------------------


def draw_ground(ax: Axes, x: float, y: float) -> None:
    """Draw ground symbol (three descending lines)."""
    lengths = [18, 12, 6]
    y_offsets = [0, -6, -12]
    for length, y_off in zip(lengths, y_offsets):
        half = length / 2
        ax.plot([x - half, x + half], [y + y_off, y + y_off], "k-", lw=LINE_WIDTH)


# ---------------------------------------------------------------------------
# Junction dot
# ---------------------------------------------------------------------------


def draw_junction(ax: Axes, x: float, y: float) -> None:
    """Draw a filled dot at a wire junction."""
    ax.plot(x, y, "ko", markersize=4)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _draw_polyline(ax: Axes, points: list[tuple[float, float]]) -> None:
    """Draw a connected line through a list of (x, y) points."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    ax.plot(xs, ys, "k-", lw=LINE_WIDTH)
