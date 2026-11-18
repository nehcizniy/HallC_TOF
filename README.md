# HallC_TOF

Generate target-to-focal-plane time-of-flight (TOF) tables for Jefferson Lab
Hall C's SHMS and HMS spectrometers.

## Run

Requires Python 3; no external packages are needed.

```bash
python3 generate_shms_tof_tables.py
python3 generate_hms_tof_tables.py
```

Optional arguments:

```bash
python3 generate_shms_tof_tables.py --path-length-m 18.1 --output-dir tables
```

Each script writes individual electron, pion, kaon, and proton tables, plus
one combined table, in both CSV and TXT formats. Files use `shms_` or `hms_`
prefixes. Outputs default to the script directory; matching files are overwritten.

## Parameters and calculation

- SHMS central path: 18.1 m; HMS central path: 22.0 m.
- Momentum: 0.5–11 GeV/c in 0.5 GeV/c steps, including both endpoints.
- TOF: nanoseconds, measured from production at the target.
- Charged pion and kaon masses are used.

```text
beta = p / sqrt(p² + m²)
TOF  = L / (beta × c)
c    = 0.299792458 m/ns
```

Here p and m are numerical values in GeV/c and GeV/c². The model assumes
constant momentum and a fixed central flight path, with no energy loss,
particle decay, or event-specific path correction. The momentum grid is a
theoretical calculation, not a statement of spectrometer operating limits.

## Files

- `common_parameters.py`: shared masses, speed of light, and momentum grid.
- `shms_parameters.py`, `hms_parameters.py`: spectrometer settings.
- `tof_functions.py`: common functions and sections reserved for future
  spectrometer-specific corrections.
- `generate_shms_tof_tables.py`, `generate_hms_tof_tables.py`: entry scripts.

## Parameter sources

Central paths match `PARAM/SHMS/GEN/pcana.param` and
`PARAM/HMS/GEN/hcana.param` in the local `hallc_replay_rsidis` configuration.
Masses use [NIST CODATA 2022](https://physics.nist.gov/cuu/pdf/wall_2022.pdf)
for the electron and PDG 2025 for the
[pion](https://pdg.lbl.gov/2025/listings/rpp2025-list-pi-plus-minus.pdf),
[kaon](https://pdg.lbl.gov/2025/listings/rpp2025-list-K-plus-minus.pdf), and
[proton](https://pdg.lbl.gov/2025/listings/rpp2025-list-p.pdf).

Validation checked all 176 TOF values using 50-digit arithmetic, agreement
between individual/combined and CSV/TXT tables, and reproducible generation
of all 20 files. Differences from the independent calculation were below
5 × 10⁻⁷ ns, consistent with six-decimal output rounding.
