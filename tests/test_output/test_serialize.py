"""Tests for output/serialize.py — CircuitRecord → JSON serialization."""

from __future__ import annotations

import json

from electronics_qa_generator.models import CircuitRecord, SimulationConfig
from electronics_qa_generator.output.serialize import record_to_dict, record_to_json
from electronics_qa_generator.templates import ALL_TEMPLATES


class TestRecordToDict:
    """record_to_dict"""

    def test_all_fields_present(self):
        """All CircuitRecord fields appear in the dict."""
        rec = CircuitRecord(
            id="test_0001",
            family="passive",
            topology="voltage_divider",
            difficulty=1,
            parameters={"R1": 1000.0},
            netlist="* test\n.end",
            simulation=SimulationConfig(type="op", params={"a": 1}),
            probes=["V(out)"],
        )
        d = record_to_dict(rec)
        assert set(d.keys()) == {
            "id",
            "family",
            "topology",
            "difficulty",
            "parameters",
            "netlist",
            "simulation",
            "probes",
        }

    def test_parameters_is_dict(self):
        rec = CircuitRecord(id="x", family="f", topology="t", difficulty=1, parameters={"k": "v"})
        d = record_to_dict(rec)
        assert d["parameters"] == {"k": "v"}

    def test_probes_is_list(self):
        rec = CircuitRecord(
            id="x", family="f", topology="t", difficulty=1, probes=["V(out)", "I(R1)"]
        )
        d = record_to_dict(rec)
        assert d["probes"] == ["V(out)", "I(R1)"]

    def test_simulation_flattened(self):
        sim = SimulationConfig(type="ac", tool="Xyce", params={"start_hz": 1})
        rec = CircuitRecord(id="x", family="f", topology="t", difficulty=1, simulation=sim)
        d = record_to_dict(rec)
        assert d["simulation"] == {"type": "ac", "tool": "Xyce", "params": {"start_hz": 1}}

    def test_simulation_none(self):
        rec = CircuitRecord(id="x", family="f", topology="t", difficulty=1, simulation=None)
        d = record_to_dict(rec)
        assert d["simulation"] is None

    def test_sampled_record_is_serializable(self):
        """A record from a real template sample serializes successfully."""
        for template in ALL_TEMPLATES:
            rec = template.sample(seed=1)
            d = record_to_dict(rec)
            # Verify required keys
            assert d["id"]
            assert d["family"]
            assert d["topology"]
            assert d["netlist"].startswith("*")
            assert d["netlist"].endswith(".end")
            assert isinstance(d["parameters"], dict)
            assert isinstance(d["probes"], list)


class TestRecordToJson:
    """record_to_json"""

    def test_output_is_valid_json(self):
        rec = CircuitRecord(id="x", family="f", topology="t", difficulty=1)
        s = record_to_json(rec)
        parsed = json.loads(s)
        assert parsed == record_to_dict(rec)

    def test_round_trip_equals_dict(self):
        rec = CircuitRecord(
            id="abc",
            family="passive",
            topology="rc_lowpass",
            difficulty=1,
            netlist=".end",
            simulation=SimulationConfig(type="ac", params={"f": 1000.0}),
            probes=["V(out)"],
        )
        s = record_to_json(rec)
        assert json.loads(s) == record_to_dict(rec)

    def test_deterministic_output(self):
        """Same record → same JSON string."""
        rec = ALL_TEMPLATES[0].sample(seed=42)
        a = record_to_json(rec)
        b = record_to_json(rec)
        assert a == b


class TestJsonRoundtrip:
    """json.loads(record_to_json(...)) recovers the dict."""

    def test_roundtrip_with_simulation(self):
        rec = CircuitRecord(
            id="rt_01",
            family="diode",
            topology="half_wave_rectifier",
            difficulty=1,
            parameters={"R1": 4700.0},
            netlist="* rectifier\n.end",
            simulation=SimulationConfig(type="tran", tool="Xyce", params={"stop_s": 0.1}),
            probes=["V(out)", "I(D1)"],
        )
        result = json.loads(record_to_json(rec))
        assert result["id"] == "rt_01"
        assert result["simulation"]["type"] == "tran"
        assert result["simulation"]["params"]["stop_s"] == 0.1
        assert result["probes"] == ["V(out)", "I(D1)"]
