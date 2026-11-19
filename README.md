# HallC_TOF

Generate target-to-focal-plane time-of-flight (TOF) tables for Jefferson Lab
Hall C's SHMS and HMS spectrometers.

## Run

Requires Python 3.8+ and ReportLab. Set up an isolated environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run both generators in that environment:

```bash
python3 generate_shms_tof_tables.py
python3 generate_hms_tof_tables.py
```

Optional arguments:

```bash
python3 generate_shms_tof_tables.py --path-length-m 18.1 --output-dir tables
```

Each script writes individual electron, pion, kaon, and proton tables, plus
one combined table, in CSV, TXT, and PDF formats. Files use `shms_` or `hms_`
prefixes. Outputs default to the script directory; matching files are overwritten.

PDFs use serif text, a compact caption, three horizontal rules, and no shading
or vertical rules. They include column units and calculation notes. Combined PDFs
are `shms_tof.pdf` and `hms_tof.pdf`; individual PDFs use the same names as
the corresponding CSV files, with a `.pdf` extension.

## ROOT plots

Run the ROOT 6 macros from this directory (no Python environment is needed):

```bash
root -l -b -q 'plot_TOF_vs_momentum_SHMS.C()'
root -l -b -q 'plot_TOF_vs_momentum_HMS.C()'
```

Each macro generates individual electron, pion, kaon, and proton plots plus
one combined plot, in PNG and vector PDF formats. Outputs are saved under
`plots/SHMS/` or `plots/HMS/`, for example
`plots/SHMS/shms_tof_vs_momentum_all.pdf`. PNGs are 1800 × 1350 pixels.

Optional arguments select the input table directory and output directory:

```bash
root -l -b -q 'plot_TOF_vs_momentum_SHMS.C(".", "my_plots/SHMS")'
```

Markers show the CSV table values; smooth curves use the relativistic TOF
formula. Masses and the speed of light are read from the individual TXT table
headers, and the path length comes from the combined CSV. The macros reject
inconsistent inputs before plotting. Keep the CSV and TXT tables together.

Plots use a logarithmic TOF (y) axis, a linear momentum (x) axis, serif labels,
and distinct colors, line styles, and markers.
Electrons are light grey (`#B3B3B3`); pions blue, kaons orange, and protons green.
Y-axis ranges span at least a factor of two to keep logarithmic ticks readable
for nearly constant curves, including electrons. Run output can be saved with
`2>&1 | tee root-run.log` (use `set -o pipefail` in shell scripts).

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
- `generate_shms_tof_tables.py`, `generate_hms_tof_tables.py`: table entry scripts.
- `plot_TOF_vs_momentum_SHMS.C`, `plot_TOF_vs_momentum_HMS.C`: ROOT plot entry macros.
- `tof_plot_functions.h`: shared ROOT plotting and input checks.

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
of all 20 CSV/TXT files. PDF validation also checked all ten documents against
the CSV tables and confirmed that each contains all 22 rows on one page.
Differences from the independent calculation were below
5 × 10⁻⁷ ns, consistent with six-decimal output rounding.
