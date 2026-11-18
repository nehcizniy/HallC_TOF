#!/usr/bin/env python3
"""Generate HMS TOF tables (CSV/TXT, times in ns).

Usage: python3 generate_hms_tof_tables.py
       python3 generate_hms_tof_tables.py --path-length-m LENGTH --output-dir tables

Writes individual particle tables plus hms_tof.csv and hms_tof.txt.
LENGTH is in meters. Defaults come from the parameter modules.
Tables are written beside this script unless --output-dir is given;
existing files with the same names are overwritten.
"""

import argparse
from pathlib import Path

# Load parameters and shared functions.
import common_parameters as common
import hms_parameters as parameters
from tof_functions import generate_tables, positive_length


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
        help="output directory (default: script directory)",
    )
    args = parser.parse_args()
    # Generate tables with the selected settings.
    generate_tables(
        args.path_length_m, args.output_dir,
        spectrometer=parameters.SPECTROMETER,
        filename_prefix=parameters.FILENAME_PREFIX,
        masses_gev_c2=common.MASSES_GEV_C2,
        momenta_gev_c=common.MOMENTA_GEV_C,
        c_m_per_ns=common.C_M_PER_NS,
    )


if __name__ == "__main__":
    main()
