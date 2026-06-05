"""Template library: circuit families, topologies, and parameter ranges.

Each template defines the topology graph, legal parameter ranges, legal
simulation types, measurable outputs, and rejection rules. Start with the MVP
families from docs/plan.md:

    voltage_divider, rc_lowpass, rc_highpass, rlc_bandpass, half_wave_rectifier

A template should expose a `sample()` method that returns a structured circuit
record (not just a netlist), per docs/plan.md section 1.5.
"""
