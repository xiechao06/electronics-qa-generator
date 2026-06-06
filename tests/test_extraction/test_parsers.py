"""Tests for extraction/parsers.py — Xyce output parsing."""

from __future__ import annotations

import pytest

from electronics_qa_generator.extraction.parsers import parse_op, parse_ac, parse_tran


# ---------------------------------------------------------------------------
# .op parser
# ---------------------------------------------------------------------------

OP_OUTPUT = """\
Index   V(out)      V(in)
------  ----------  ----------
     0  3.14159     5.00000
"""


class TestParseOp:
    def test_single_probe(self):
        result = parse_op(OP_OUTPUT)
        assert result.get("V(OUT)") == pytest.approx(3.14159)
        assert result.get("V(IN)") == pytest.approx(5.0)

    def test_empty_input(self):
        assert parse_op("") == {}

    def test_malformed_input(self):
        assert parse_op("garbage\ndata\nno headers") == {}


# ---------------------------------------------------------------------------
# .ac parser
# ---------------------------------------------------------------------------

AC_OUTPUT = """\
Index   FREQ            V(out)
------  --------        ----------
     0  1.000000e+01    9.999987e-01
     1  1.258925e+01    9.999978e-01
     2  1.584893e+01    9.999965e-01
"""


class TestParseAc:
    def test_three_point_sweep(self):
        result = parse_ac(AC_OUTPUT)
        assert "V(OUT)" in result
        data = result["V(OUT)"]
        assert len(data) == 3
        assert data[0] == pytest.approx((10.0, 0.9999987))

    def test_frequencies_in_ascending_order(self):
        result = parse_ac(AC_OUTPUT)
        freqs = [f for f, _ in result["V(OUT)"]]
        assert freqs == sorted(freqs)

    def test_empty_input(self):
        assert parse_ac("") == {}

    def test_malformed_input(self):
        assert parse_ac("no valid data here") == {}


# ---------------------------------------------------------------------------
# .ac complex parser (single-frequency phasor)
# ---------------------------------------------------------------------------

AC_COMPLEX_OUTPUT = """\
Index       FREQ           Re(V(OUT))        Im(V(OUT))    
0        2.75800000e+04    7.20167638e-07   -8.48626607e-04
"""


class TestParseAcComplex:
    """Tests for parse_ac_complex — preserves Re/Im as complex numbers."""

    def test_returns_complex_phasor(self):
        from electronics_qa_generator.extraction.parsers import parse_ac_complex

        result = parse_ac_complex(AC_COMPLEX_OUTPUT)
        assert "V(OUT)" in result
        data = result["V(OUT)"]
        assert len(data) == 1
        freq, v_c = data[0]
        assert freq == pytest.approx(27580.0)
        assert isinstance(v_c, complex)
        assert v_c.real == pytest.approx(7.20167638e-07)
        assert v_c.imag == pytest.approx(-8.48626607e-04)
        assert abs(v_c) > 0
        import math
        import cmath

        assert cmath.phase(v_c) == pytest.approx(-math.pi / 2, abs=0.001)

    def test_empty_input(self):
        from electronics_qa_generator.extraction.parsers import parse_ac_complex

        assert parse_ac_complex("") == {}

    def test_malformed_input(self):
        from electronics_qa_generator.extraction.parsers import parse_ac_complex

        assert parse_ac_complex("no valid data here") == {}


# ---------------------------------------------------------------------------
# .tran parser
# ---------------------------------------------------------------------------

TRAN_OUTPUT = """\
Index   TIME            V(out)          V(in)
------  --------        ----------      ----------
     0  0.000000e+00    0.000000e+00    0.000000e+00
     1  1.666667e-05    8.543210e-02    6.226000e+00
     2  3.333333e-05    1.708642e-01    6.226000e+00
"""


class TestParseTran:
    def test_two_probes(self):
        result = parse_tran(TRAN_OUTPUT)
        assert "V(OUT)" in result
        assert "V(IN)" in result
        assert len(result["V(OUT)"]) == 3
        assert len(result["V(IN)"]) == 3

    def test_time_values_increasing(self):
        result = parse_tran(TRAN_OUTPUT)
        times = [t for t, _ in result["V(OUT)"]]
        assert times == sorted(times)

    def test_value_at_first_time(self):
        result = parse_tran(TRAN_OUTPUT)
        assert result["V(OUT)"][0][1] == pytest.approx(0.0)

    def test_empty_input(self):
        assert parse_tran("") == {}

    def test_malformed_input(self):
        assert parse_tran("no valid data") == {}
