## ADDED Requirements

### Requirement: Fact extractor registry
The system SHALL provide a registry `FACT_EXTRACTORS: dict[str, Callable]` mapping topology name to a fact-extraction function. Each function SHALL accept parsed simulation output and component parameters, and return a `dict[str, Any]` of canonical facts.

#### Scenario: Registry has extractors for existing topologies
- **WHEN** the system is loaded
- **THEN** `FACT_EXTRACTORS` contains keys for `"voltage_divider"`, `"rc_lowpass"`, `"rc_highpass"`, `"rlc_bandpass"`, and `"half_wave_rectifier"`

### Requirement: Voltage divider fact extraction
The system SHALL provide an extractor that computes DC output voltage and divider ratio from `.op` parsed data. The fact dict SHALL include `Vout_dc` (float) and `divider_ratio` (float, Vout/Vin).

#### Scenario: Extracted facts include Vout_dc
- **WHEN** the voltage divider extractor is called with parsed OP data and parameters
- **THEN** the result contains `"Vout_dc"` — a numeric value in volts

### Requirement: RC low-pass fact extraction
The system SHALL provide an extractor that computes cutoff frequency (`cutoff_hz`), passband gain in dB (`passband_gain_db`), and behavior classification (`"behavior"`: `"low-pass"`) from `.ac` sweep data.

#### Scenario: Cutoff frequency is found
- **WHEN** the RC low-pass extractor processes a sweep with clear roll-off
- **THEN** `cutoff_hz` is a positive float
- **AND** `passband_gain_db` is approximately 0 dB (within ±0.5 dB)
- **AND** `behavior` is `"low-pass"`

### Requirement: RC high-pass fact extraction
The system SHALL provide an extractor analogous to low-pass, computing `cutoff_hz`, `passband_gain_db` (at high frequencies), and `behavior` (`"high-pass"`).

### Requirement: RLC band-pass fact extraction
The system SHALL provide an extractor computing `center_freq_hz`, `bandwidth_hz`, quality factor `Q`, and `peak_gain_db`.

#### Scenario: Band-pass facts include center frequency and bandwidth
- **WHEN** the RLC band-pass extractor processes a resonance curve
- **THEN** `center_freq_hz` is near the peak of the curve
- **AND** `bandwidth_hz` spans the −3 dB points around the peak

### Requirement: Half-wave rectifier fact extraction
The system SHALL provide an extractor computing `Vout_peak` (peak output voltage), `Vout_dc` (average DC level), and `ripple_vpp` (peak-to-peak ripple) from steady-state `.tran` data.

#### Scenario: Ripple is non-zero
- **WHEN** the rectifier extractor processes transient data with a filter capacitor
- **THEN** `ripple_vpp` is positive (not zero)

### Requirement: Cutoff frequency algorithm
The system SHALL provide a shared helper `find_cutoff_frequency(freqs: list[float], gains_db: list[float]) -> float` that returns the frequency at which gain has dropped by 3 dB from the passband reference. For a high-pass, the reference is the maximum gain; for a low-pass, the reference is the gain at the lowest frequency.

#### Scenario: Cutoff found in clean AC sweep
- **WHEN** a low-pass with known theoretical cutoff of 1.59 kHz is swept
- **THEN** `find_cutoff_frequency` returns a value within 5% of 1590 Hz
