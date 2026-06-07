"""Template library: circuit families, topologies, and parameter ranges.

Each template defines the topology graph, legal parameter ranges, legal
simulation types, measurable outputs, and rejection rules.

MVP families (see docs/plan.md):
    voltage_divider, rc_lowpass, rc_highpass, rlc_bandpass, half_wave_rectifier

Usage:
    >>> from electronics_qa_generator.templates import ALL_TEMPLATES
    >>> for t in ALL_TEMPLATES:
    ...     record = t.sample(seed=42)
"""

from .dc_mesh import DCMultisourceMesh
from .schaums_opamp import OpAmpInvInputFb
from .schaums_new import (
    OpAmpNoninverting,
    OpAmpDifference,
    OpAmpSumming,
    DCCurrentDivider,
    ACRLSeries,
    DCNodalCurrentSource,
)
from .base import CircuitTemplate
from .e_series import E12_VALUES, E6_VALUES, INDUCTOR_VALUES, pick_e_value
from .netlist_helpers import format_netlist
from .parameter import Choice, LogUniform, Uniform
from .passive import RCLowPass, RCHighPass, RLCBandPass, VoltageDivider
from .rectifier import HalfWaveRectifier
from .transient import RCStepResponse, RLStepResponse
from .ac_phasor import ACPhasorRC
from .bjt import BJTCEAmplifier, BJTEFollower
from .mosfet import MOSFETCSAmplifier
from .network import ResistorNetwork
from .op_amp import OpAmpInverting
from .rlc_resonance import RLCSeriesResonance

ALL_TEMPLATES: list[CircuitTemplate] = [
    VoltageDivider(),
    RCLowPass(),
    RCHighPass(),
    RLCBandPass(),
    HalfWaveRectifier(),
    RCStepResponse(),
    RLStepResponse(),
    ACPhasorRC(),
    BJTCEAmplifier(),
    BJTEFollower(),
    MOSFETCSAmplifier(),
    ResistorNetwork(),
    OpAmpInverting(),
    RLCSeriesResonance(),
    DCMultisourceMesh(),
    OpAmpInvInputFb(),
    OpAmpNoninverting(),
    OpAmpDifference(),
    OpAmpSumming(),
    DCCurrentDivider(),
    ACRLSeries(),
    DCNodalCurrentSource(),
]
"""Registry of all concrete template instances.

The downstream sampler stage iterates over this list to drive circuit generation.
"""

__all__ = [
    # Base
    "CircuitTemplate",
    # Distributions
    "Uniform",
    "LogUniform",
    "Choice",
    # E-series
    "E6_VALUES",
    "E12_VALUES",
    "INDUCTOR_VALUES",
    "pick_e_value",
    # Netlist
    "format_netlist",
    # Templates
    "VoltageDivider",
    "RCLowPass",
    "RCHighPass",
    "RLCBandPass",
    "HalfWaveRectifier",
    # Registry
    "ALL_TEMPLATES",
]
