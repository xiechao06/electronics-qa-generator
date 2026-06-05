"""Tests for render/schematic.py — full schematic PNG rendering."""

from __future__ import annotations


from PIL import Image

from electronics_qa_generator.graph.models import CircuitGraph
from electronics_qa_generator.render.format import format_component_label
from electronics_qa_generator.render.schematic import render_schematic


def _build_voltage_divider() -> CircuitGraph:
    g = CircuitGraph(
        family="passive",
        topology="voltage_divider",
        header_comment="* Voltage divider",
    )
    g.add_voltage_source("Vin", "in", "0", dc=5)
    g.add_resistor("R1", "in", "out", 4700)
    g.add_resistor("R2", "out", "0", 10000)
    return g


def _build_rc_lowpass() -> CircuitGraph:
    g = CircuitGraph(
        family="passive",
        topology="rc_lowpass",
        header_comment="* RC low-pass filter",
    )
    g.add_voltage_source("Vin", "in", "0", ac=1)
    g.add_resistor("R1", "in", "out", 1000)
    g.add_capacitor("C1", "out", "0", 1e-7)
    return g


def _build_rc_highpass() -> CircuitGraph:
    g = CircuitGraph(
        family="passive",
        topology="rc_highpass",
        header_comment="* RC high-pass filter",
    )
    g.add_voltage_source("Vin", "in", "0", ac=1)
    g.add_capacitor("C1", "in", "out", 1e-7)
    g.add_resistor("R1", "out", "0", 1000)
    return g


def _build_rlc_bandpass() -> CircuitGraph:
    g = CircuitGraph(
        family="passive",
        topology="rlc_bandpass",
        header_comment="* RLC band-pass filter",
    )
    g.add_voltage_source("Vin", "in", "0", ac=1)
    g.add_resistor("R1", "in", "n1", 47)
    g.add_inductor("L1", "n1", "out", 0.01)
    g.add_capacitor("C1", "out", "0", 1e-6)
    return g


def _build_half_wave_rectifier() -> CircuitGraph:
    g = CircuitGraph(
        family="diode",
        topology="half_wave_rectifier",
        header_comment="* Half-wave rectifier",
    )
    g.add_voltage_source("Vin", "in", "0", sin={"amplitude": 5, "freq": 60})
    g.add_diode("D1", "in", "out", model="D1N4148")
    g.add_capacitor("C1", "out", "0", 4.7e-5)
    g.add_resistor("Rload", "out", "0", 1000)
    return g


# ---------------------------------------------------------------------------
# Rendering tests
# ---------------------------------------------------------------------------


class TestRenderSchematic:
    def test_voltage_divider(self, tmp_path):
        g = _build_voltage_divider()
        out = tmp_path / "vd.png"
        render_schematic(g, out)
        assert out.exists()
        img = Image.open(out)
        assert img.width >= 800
        assert img.height >= 400
        assert img.mode in ("RGB", "RGBA")

    def test_rc_lowpass(self, tmp_path):
        g = _build_rc_lowpass()
        out = tmp_path / "rc_lp.png"
        render_schematic(g, out)
        assert out.exists()
        img = Image.open(out)
        assert img.width >= 800
        assert img.height >= 400

    def test_rc_highpass(self, tmp_path):
        g = _build_rc_highpass()
        out = tmp_path / "rc_hp.png"
        render_schematic(g, out)
        assert out.exists()
        img = Image.open(out)
        assert img.width >= 800

    def test_rlc_bandpass(self, tmp_path):
        g = _build_rlc_bandpass()
        out = tmp_path / "rlc.png"
        render_schematic(g, out)
        assert out.exists()
        img = Image.open(out)
        assert img.width >= 800

    def test_half_wave_rectifier(self, tmp_path):
        g = _build_half_wave_rectifier()
        out = tmp_path / "hw.png"
        render_schematic(g, out)
        assert out.exists()
        img = Image.open(out)
        assert img.width >= 800

    def test_determinism(self, tmp_path):
        g = _build_voltage_divider()
        out1 = tmp_path / "vd1.png"
        out2 = tmp_path / "vd2.png"
        render_schematic(g, out1)
        render_schematic(g, out2)
        assert out1.read_bytes() == out2.read_bytes()

    def test_non_empty_content(self, tmp_path):
        g = _build_voltage_divider()
        out = tmp_path / "vd.png"
        render_schematic(g, out)
        # Should have non-trivial content (not just white pixels)
        img = Image.open(out)
        bbox = img.getbbox()
        # getbbox() returns None for all-white images
        assert bbox is not None
        assert bbox[2] - bbox[0] > 100


# ---------------------------------------------------------------------------
# Label formatting tests
# ---------------------------------------------------------------------------


class TestFormatComponentLabel:
    def test_resistor_kilo(self):
        label = format_component_label("R1", "resistor", {"value": 4700})
        assert "4.7k" in label
        assert "Ω" in label
        assert "R1" in label

    def test_resistor_small(self):
        label = format_component_label("R2", "resistor", {"value": 47})
        assert "47 Ω" in label or "47Ω" in label

    def test_capacitor_nano(self):
        label = format_component_label("C1", "capacitor", {"value": 1e-7})
        assert "100n" in label
        assert "F" in label
        assert "C1" in label

    def test_capacitor_micro(self):
        label = format_component_label("C1", "capacitor", {"value": 4.7e-6})
        assert "4.7u" in label or "4.7μ" in label
        assert "F" in label

    def test_inductor_milli(self):
        label = format_component_label("L1", "inductor", {"value": 0.01})
        assert "10m" in label
        assert "H" in label
        assert "L1" in label

    def test_vsource_dc(self):
        label = format_component_label("V1", "vsource", {"dc": 5})
        assert "5V" in label or "5 V" in label
        assert "DC" in label

    def test_vsource_ac(self):
        label = format_component_label("Vin", "vsource", {"ac": 1})
        assert "1V" in label.replace(" ", "") or "1 V" in label
        assert "AC" in label

    def test_diode_with_model(self):
        label = format_component_label("D1", "diode", {"model": "D1N4148"})
        assert "D1N4148" in label
        assert "D1" in label
