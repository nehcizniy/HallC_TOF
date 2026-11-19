"""TOF calculations and table output; settings are passed as arguments."""

import argparse
import csv
import json
import math
import shutil
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


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


def write_pdf_table(path, title, headers, rows, notes):
    """Write a paper-style table with serif text and three horizontal rules."""
    labels = {"momentum_GeV_c": "Momentum\n(GeV/c)",
              "path_length_m": "Path length\n(m)", "tof_ns": "TOF\n(ns)"}
    headings = [labels.get(h, h.replace("_tof_ns", "").capitalize() + "\nTOF (ns)")
                for h in headers]
    caption_style = ParagraphStyle("Caption", fontName="Times-Roman", fontSize=11,
                                   leading=14, spaceAfter=10)
    note_style = ParagraphStyle("Notes", fontName="Times-Roman", fontSize=9,
                                leading=12)
    # Keep individual tables compact; allow more width for combined tables.
    width = 330 if len(headers) == 3 else 504
    margin = (letter[0] - width) / 2
    document = SimpleDocTemplate(
        str(path), pagesize=letter, rightMargin=margin, leftMargin=margin,
        topMargin=54, bottomMargin=54, title=title, author="HallC_TOF",
        invariant=1,
    )
    table = Table([headings, *rows], colWidths=[width / len(headers)] * len(headers),
                  repeatRows=1, hAlign="CENTER")
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Times-Roman"),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
    ]))
    caption = (f"<b>TABLE I.</b> {escape(title)} from the target to the "
               f"focal-plane center. {escape(notes[0])}")
    caption = caption.replace("GeV/c^2", "GeV/<i>c</i><super>2</super>")
    story = [Paragraph(caption, caption_style), table, Spacer(1, 8)]
    # Typeset the existing formula and units without changing the calculation.
    formula = escape(notes[1]).replace("TOF", "<i>t</i>").replace("beta", "β")
    formula = formula.replace("sqrt(p^2 + m^2)", "√(p<super>2</super> + m<super>2</super>)")
    formula = formula.replace("*", " ")
    story.extend([
        Paragraph("<i>Notes.</i> " + formula, note_style),
        Paragraph("Constant momentum and central path; no energy loss, decay, or "
                  "event-specific path correction. Printed digits do not indicate "
                  "experimental precision.", note_style),
    ])
    document.build(story)


def generate_tables(path_length_m, output_dir, *, spectrometer, filename_prefix,
                    masses_gev_c2, momenta_gev_c, c_m_per_ns):
    """Write individual and combined CSV/TXT/PDF tables; overwrite matching files."""
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
        # Write a PDF from the same formatted data.
        pdf_path = output_dir / f"{filename_prefix}{particle}_tof.pdf"
        write_pdf_table(
            pdf_path, f"{spectrometer} {particle} time of flight",
            ["momentum_GeV_c", "path_length_m", "tof_ns"], rows,
            [f"Path length: {path_length_m:.12g} m; mass: {mass:.11g} GeV/c^2.",
             f"TOF = L/(beta*c); beta = p/sqrt(p^2 + m^2); c = {c_m_per_ns:.12g} m/ns."],
        )
        print(f"Wrote {csv_path}, {txt_path}, and {pdf_path} ({len(rows)} rows each)")

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
    pdf_path = output_dir / f"{filename_prefix}tof.pdf"
    write_pdf_table(
        pdf_path, f"{spectrometer} time of flight for all particles", headers, combined_rows,
        [f"Path length: {path_length_m:.12g} m.",
         f"TOF = L/(beta*c); beta = p/sqrt(p^2 + m^2); c = {c_m_per_ns:.12g} m/ns."],
    )
    print(f"Wrote {csv_path}, {txt_path}, and {pdf_path} ({len(combined_rows)} rows each)")


def plot_command(table_dir, output_dir, *, spectrometer):
    """Prepare a batch ROOT command using the shared plot style."""
    if spectrometer not in ("SHMS", "HMS"):
        raise ValueError("spectrometer must be SHMS or HMS")
    root = shutil.which("root")
    if root is None:
        raise RuntimeError("ROOT is not on PATH; set up ROOT or use --tables-only.")
    macro = Path(__file__).resolve().parent / f"plot_TOF_vs_momentum_{spectrometer}.C"
    header = macro.with_name("tof_plot_functions.h")
    if not macro.is_file() or not header.is_file():
        raise RuntimeError("Keep the ROOT macros and tof_plot_functions.h beside the Python scripts.")
    # Quote C++ string arguments; execute directly without a shell.
    arguments = ", ".join(json.dumps(str(Path(p).resolve()), ensure_ascii=False)
                          for p in (table_dir, output_dir))
    return [root, "-l", "-b", "-q", f"{macro}({arguments})"]


def generate_plots(command):
    """Run the prepared ROOT command and stream its progress."""
    print("Generating PNG/PDF plots with the shared ROOT macros...", flush=True)
    try:
        subprocess.run(command, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"ROOT plot generation failed: {exc}") from exc


# 2. SHMS-specific functions: reserved for future corrections.


# 3. HMS-specific functions: reserved for future corrections.
