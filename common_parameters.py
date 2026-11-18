"""Shared physics constants and momentum grid.

Masses: NIST CODATA 2022 (electron); PDG 2025 (hadrons).
"""

# Speed of light (m/ns).
C_M_PER_NS = 0.299792458

# Rest masses (GeV/c^2); charged pions and kaons.
MASSES_GEV_C2 = {
    "electron": 0.00051099895069,
    "pion": 0.13957039,
    "kaon": 0.493677,
    "proton": 0.93827208816,
}

# Momentum grid: 0.5-11 GeV/c in 0.5 steps.
MOMENTA_GEV_C = tuple(i / 2 for i in range(1, 23))
