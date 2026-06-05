"""Tests for render/svg_render.py — fill, rasterize."""

from __future__ import annotations

from PIL import Image

from electronics_qa_generator.graph.models import CircuitGraph
from electronics_qa_generator.render.schematic import render_schematic
from electronics_qa_generator.render.svg_render import fill_template, render_svg_schematic
from electronics_qa_generator.render.svg_templates import registry as default_registry


# -- Task 6.4: PNG output for all 5 MVP topologies ---------------------------


class TestSVGRenderOutput:
    def test_voltage_divider_png(self, tmp_path):
        g = _build_voltage_divider()
        tpl = default_registry.resolve(g)
        out = tmp_path / "vd.png"
        render_svg_schematic(g, tpl, out)
        assert out.exists()
        img = Image.open(out)
        assert img.width >= 800
        assert img.height >= 400

    def test_rc_lowpass_png(self, tmp_path):
        g = _build_rc_lowpass()
        tpl = default_registry.resolve(g)
        out = tmp_path / "rc_lp.png"
        render_svg_schematic(g, tpl, out)
        assert out.exists()
        assert Image.open(out).width >= 800

    def test_rc_highpass_png(self, tmp_path):
        g = _build_rc_highpass()
        tpl = default_registry.resolve(g)
        out = tmp_path / "rc_hp.png"
        render_svg_schematic(g, tpl, out)
        assert out.exists()
        assert Image.open(out).width >= 800

    def test_rlc_bandpass_png(self, tmp_path):
        g = _build_rlc_bandpass()
        tpl = default_registry.resolve(g)
        out = tmp_path / "rlc.png"
        render_svg_schematic(g, tpl, out)
        assert out.exists()
        assert Image.open(out).width >= 800

    def test_half_wave_rectifier_png(self, tmp_path):
        g = _build_half_wave_rectifier()
        tpl = default_registry.resolve(g)
        out = tmp_path / "hw.png"
        render_svg_schematic(g, tpl, out)
        assert out.exists()
        assert Image.open(out).width >= 800


# -- Task 6.5: Determinism ----------------------------------------------------


class TestSVGRenderDeterminism:
    def test_two_renders_identical(self, tmp_path):
        g = _build_voltage_divider()
        tpl = default_registry.resolve(g)
        out1 = tmp_path / "a.png"
        out2 = tmp_path / "b.png"
        render_svg_schematic(g, tpl, out1)
        render_svg_schematic(g, tpl, out2)
        assert out1.read_bytes() == out2.read_bytes()


# -- Task 6.3: Fill template populates slots correctly ------------------------


class TestFillTemplate:
    def test_component_values_populated(self):
        g = _build_voltage_divider()
        tpl = default_registry.resolve(g)
        filled = fill_template(g, tpl)
        assert "4.7k" in filled  # R1 value
        assert "10k" in filled  # R2 value
        assert "5V" in filled  # Vin DC value

    def test_node_labels_populated(self):
        g = _build_voltage_divider()
        tpl = default_registry.resolve(g)
        filled = fill_template(g, tpl)
        # Node labels appear in the SVG text
        assert ">in<" in filled.replace(" ", "")
        assert ">out<" in filled.replace(" ", "")

    def test_labels_use_format_component_label(self):
        """Labels match the same formatting used by the matplotlib path."""
        g = _build_rc_lowpass()
        tpl = default_registry.resolve(g)
        filled = fill_template(g, tpl)
        assert "100n" in filled and "F" in filled  # capacitor
        assert "1k" in filled  # resistor


# -- Task 6.6: Fallback for unregistered topology ----------------------------


class TestRenderSchematicFallback:
    def test_unregistered_topology_falls_back_to_matplotlib(self, tmp_path):
        g = CircuitGraph(family="custom", topology="unknown")
        g.add_voltage_source("V1", "in", "0", dc=5)
        g.add_resistor("R1", "in", "out", 1000)
        g.add_resistor("R2", "out", "0", 1000)
        out = tmp_path / "fallback.png"
        render_schematic(g, out)
        assert out.exists()
        img = Image.open(out)
        assert img.width >= 800


# -- Helpers (matching test_schematic.py builders) ----------------------------


def _build_voltage_divider() -> CircuitGraph:
    g = CircuitGraph(family="passive", topology="voltage_divider")
    g.add_voltage_source("Vin", "in", "0", dc=5)
    g.add_resistor("R1", "in", "out", 4700)
    g.add_resistor("R2", "out", "0", 10000)
    return g


def _build_rc_lowpass() -> CircuitGraph:
    g = CircuitGraph(family="passive", topology="rc_lowpass")
    g.add_voltage_source("Vin", "in", "0", ac=1)
    g.add_resistor("R1", "in", "out", 1000)
    g.add_capacitor("C1", "out", "0", 1e-7)
    return g


def _build_rc_highpass() -> CircuitGraph:
    g = CircuitGraph(family="passive", topology="rc_highpass")
    g.add_voltage_source("Vin", "in", "0", ac=1)
    g.add_capacitor("C1", "in", "out", 1e-7)
    g.add_resistor("R1", "out", "0", 1000)
    return g


def _build_rlc_bandpass() -> CircuitGraph:
    g = CircuitGraph(family="passive", topology="rlc_bandpass")
    g.add_voltage_source("Vin", "in", "0", ac=1)
    g.add_resistor("R1", "in", "n1", 47)
    g.add_inductor("L1", "n1", "out", 0.01)
    g.add_capacitor("C1", "out", "0", 1e-6)
    return g


def _build_half_wave_rectifier() -> CircuitGraph:
    g = CircuitGraph(family="diode", topology="half_wave_rectifier")
    g.add_voltage_source("Vin", "in", "0", sin={"amplitude": 5, "freq": 60})
    g.add_diode("D1", "in", "out")
    g.add_capacitor("C1", "out", "0", 4.7e-5)
    g.add_resistor("Rload", "out", "0", 1000)
    return g
