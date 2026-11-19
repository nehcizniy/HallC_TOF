// Usage: root -l -b -q 'plot_TOF_vs_momentum_SHMS.C()'
// Optional: plot_TOF_vs_momentum_SHMS.C("table_directory", "output_directory")
// Defaults: tables beside this macro; PNG/PDF plots in plots/SHMS.
#include "tof_plot_functions.h"

void plot_TOF_vs_momentum_SHMS(const char* table_directory = "", const char* output_directory = "") {
    HallCTOF::Plot("SHMS", "shms", __FILE__, table_directory, output_directory);
}
