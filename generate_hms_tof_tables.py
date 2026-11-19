#!/usr/bin/env python3
"""Generate HMS TOF tables and matching ROOT-style plots (times in ns).

Setup: python3 -m pip install -r requirements.txt; ROOT 6 must be on PATH.

Usage: python3 generate_hms_tof_tables.py
       python3 generate_hms_tof_tables.py --path-length-m LENGTH --output-dir results
       python3 generate_hms_tof_tables.py --tables-only

Writes individual and combined hms_tof tables in CSV, TXT, and PDF formats.
Plots use the same ROOT macros and style, under OUTPUT_DIR/plots/HMS.
LENGTH is in meters. Defaults come from the parameter modules.
Tables go under OUTPUT_DIR/tables/HMS. OUTPUT_DIR defaults to this script directory;
existing files with the same names are overwritten.
"""

import argparse
from pathlib import Path

# Load parameters and shared functions.
import common_parameters as common
import hms_parameters as parameters
from tof_functions import generate_plots, generate_tables, plot_command, positive_length


def main():
    # Parse command-line options.
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--path-length-m", default=parameters.PATH_LENGTH_M, type=positive_length,
        help=f"trajectory length in meters (default: {parameters.PATH_LENGTH_M:g} m)",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path(__file__).resolve().parent,
        help="base directory for tables/ and plots/ (default: script directory)",
    )
    parser.add_argument(
        "--tables-only", action="store_true", help="skip ROOT plots and generate only tables",
    )
    args = parser.parse_args()
    table_dir = args.output_dir / "tables" / parameters.SPECTROMETER
    # Check plotting dependencies before writing output files.
    command = None
    if not args.tables_only:
        try:
            command = plot_command(
                table_dir, args.output_dir / "plots" / parameters.SPECTROMETER,
                spectrometer=parameters.SPECTROMETER,
            )
        except (ValueError, RuntimeError) as exc:
            parser.error(str(exc))
    # Generate tables with the selected settings.
    generate_tables(
        args.path_length_m, table_dir,
        spectrometer=parameters.SPECTROMETER,
        filename_prefix=parameters.FILENAME_PREFIX,
        masses_gev_c2=common.MASSES_GEV_C2,
        momenta_gev_c=common.MOMENTA_GEV_C,
        c_m_per_ns=common.C_M_PER_NS,
    )

    if command is not None:
        try:
            generate_plots(command)
        except RuntimeError as exc:
            parser.exit(1, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    main()
