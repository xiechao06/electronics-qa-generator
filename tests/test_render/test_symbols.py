"""Tests for render/symbols.py — each symbol draws expected patches."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _count_patches_and_lines(ax):
    """Return (patch_count, line_count) for an axis."""
    patch_count = len(ax.patches)
    line_count = len(ax.lines)
    return patch_count, line_count


class TestSymbols:
    def test_draw_resistor(self):
        from electronics_qa_generator.render.symbols import draw_resistor

        fig, ax = plt.subplots()
        draw_resistor(ax, 200, 300, angle=0)
        patches, lines = _count_patches_and_lines(ax)
        # Resistor is a polyline (1 line), plus leads
        assert lines >= 1
        plt.close(fig)

    def test_draw_capacitor(self):
        from electronics_qa_generator.render.symbols import draw_capacitor

        fig, ax = plt.subplots()
        draw_capacitor(ax, 200, 300, angle=0)
        patches, lines = _count_patches_and_lines(ax)
        # Capacitor: 2 plates (2 lines) + 2 leads (2 lines) = 4 lines
        assert lines == 4
        plt.close(fig)

    def test_draw_inductor(self):
        from electronics_qa_generator.render.symbols import draw_inductor

        fig, ax = plt.subplots()
        draw_inductor(ax, 200, 300, angle=0)
        lines = len(ax.lines)
        assert lines >= 1
        plt.close(fig)

    def test_draw_diode(self):
        from electronics_qa_generator.render.symbols import draw_diode

        fig, ax = plt.subplots()
        draw_diode(ax, 200, 300, angle=0)
        patches, lines = _count_patches_and_lines(ax)
        # Diode: triangle (1 patch) + bar (1 line) + 2 leads (2 lines) = 1 patch, 3 lines
        assert patches == 1
        assert lines >= 2
        plt.close(fig)

    def test_draw_voltage_source(self):
        from electronics_qa_generator.render.symbols import draw_voltage_source

        fig, ax = plt.subplots()
        draw_voltage_source(ax, 200, 300, angle=0)
        patches, lines = _count_patches_and_lines(ax)
        # Voltage source: 1 circle patch + 2 leads
        assert patches >= 1
        assert lines >= 2
        plt.close(fig)

    def test_draw_ground(self):
        from electronics_qa_generator.render.symbols import draw_ground

        fig, ax = plt.subplots()
        draw_ground(ax, 200, 300)
        # Ground: 3 horizontal lines
        assert len(ax.lines) == 3
        plt.close(fig)
