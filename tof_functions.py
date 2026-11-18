"""TOF calculations and table output; settings are passed as arguments."""

import argparse
import csv
import math
from pathlib import Path


# 1. Common functions: input validation, TOF calculation, and table output.
def positive_length(value):
    """Validate a positive, finite path length in meters."""
    try:
        length = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("path length must be a number") from exc
    if not math.isfinite(length) or length <= 0:
        raise argparse.ArgumentTypeError("path length must be finite and > 0 m")
    return length


def tof_ns(momentum_gev_c, mass_gev_c2, path_length_m, *, c_m_per_ns):
    """Compute TOF = L/(beta*c) in ns, with p in GeV/c and mass in GeV/c^2."""
    beta = momentum_gev_c / math.hypot(momentum_gev_c, mass_gev_c2)
    return path_length_m / (beta * c_m_per_ns)


def generate_tables(path_length_m, output_dir, *, spectrometer, filename_prefix,
                    masses_gev_c2, momenta_gev_c, c_m_per_ns):
    """Write individual and combined CSV/TXT tables; overwrite matching files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    particle_rows = {}
    for particle, mass in masses_gev_c2.items():
        # Calculate TOF over the momentum grid.
        rows = [
            (f"{p:.1f}", f"{path_length_m:.12g}",
             f"{tof_ns(p, mass, path_length_m, c_m_per_ns=c_m_per_ns):.6f}")
            for p in momenta_gev_c
        ]
        particle_rows[particle] = rows
        # Write CSV data.
        csv_path = output_dir / f"{filename_prefix}{particle}_tof.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["momentum_GeV_c", "path_length_m", "tof_ns"])
            writer.writerows(rows)

        # Write a readable TXT table.
        txt_path = output_dir / f"{filename_prefix}{particle}_tof.txt"
        with txt_path.open("w", encoding="utf-8") as stream:
            stream.write(f"# {spectrometer} {particle}: target to focal-plane center\n")
            stream.write(f"# Mass: {mass:.11g} GeV/c^2; path length: {path_length_m:.12g} m\n")
            stream.write("# Constant momentum and fixed trajectory length; no energy loss or decay.\n")
            stream.write("# Absolute TOF for the supplied path; no event-specific path correction.\n")
            stream.write(f"# TOF = L/(beta*c); beta = p/sqrt(p^2 + m^2); c = {c_m_per_ns:.12g} m/ns\n")
            stream.write(f"{'momentum_GeV_c':>16} {'path_length_m':>16} {'tof_ns':>16}\n")
            for row in rows:
                stream.write(" ".join(f"{value:>16}" for value in row) + "\n")
        print(f"Wrote {csv_path} and {txt_path} ({len(rows)} rows each)")


    # Combine particle TOFs into one row per momentum.
    headers = ["momentum_GeV_c", "path_length_m"]
    headers.extend(f"{particle}_tof_ns" for particle in particle_rows)
    combined_rows = [
        (*group[0][:2], *(row[2] for row in group))
        for group in zip(*particle_rows.values())
    ]
    csv_path = output_dir / f"{filename_prefix}tof.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(combined_rows)

    txt_path = output_dir / f"{filename_prefix}tof.txt"
    with txt_path.open("w", encoding="utf-8") as stream:
        stream.write(f"# {spectrometer}: all particles, target to focal-plane center\n")
        stream.write(f"# Path length: {path_length_m:.12g} m; absolute TOF in ns.\n")
        stream.write("# Constant momentum and fixed path; no energy loss or decay.\n")
        stream.write(" ".join(f"{header:>16}" for header in headers) + "\n")
        for row in combined_rows:
            stream.write(" ".join(f"{value:>16}" for value in row) + "\n")
    print(f"Wrote {csv_path} and {txt_path} ({len(combined_rows)} rows each)")


# 2. SHMS-specific functions: reserved for future corrections.


# 3. HMS-specific functions: reserved for future corrections.
