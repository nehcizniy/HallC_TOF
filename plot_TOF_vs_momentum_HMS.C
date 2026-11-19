// Usage: root -l -b -q 'plot_TOF_vs_momentum_HMS.C()'
// Optional: plot_TOF_vs_momentum_HMS.C("table_directory", "output_directory")
// Defaults: tables beside this macro; PNG/PDF plots in plots/HMS.
#include "tof_plot_functions.h"

void plot_TOF_vs_momentum_HMS(const char* table_directory = "", const char* output_directory = "") {
    HallCTOF::Plot("HMS", "hms", __FILE__, table_directory, output_directory);
}
