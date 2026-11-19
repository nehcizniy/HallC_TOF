#ifndef HALLC_TOF_PLOT_FUNCTIONS_H
#define HALLC_TOF_PLOT_FUNCTIONS_H

#include <TCanvas.h>
#include <TColor.h>
#include <TF1.h>
#include <TGraph.h>
#include <TGaxis.h>
#include <TLine.h>
#include <TPad.h>
#include <TH1F.h>
#include <TLatex.h>
#include <TLegend.h>
#include <TString.h>
#include <TSystem.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace HallCTOF {

// Shared input and style definitions for both spectrometers.
static const std::array<const char*, 4> particles = {{"electron", "pion", "kaon", "proton"}};
static const std::array<const char*, 4> labels = {{"Electron", "Pion", "Kaon", "Proton"}};
static const std::array<const char*, 4> colors = {{"#B3B3B3", "#0072B2", "#D55E00", "#009E73"}};
static const std::array<int, 4> lineStyles = {{1, 2, 7, 9}};
static const std::array<double, 4> dashPixels = {{0, 6, 10, 40}};
static const std::array<double, 4> gapPixels = {{0, 6, 10, 10}};
static const double markerSize = 1.2;
static const std::array<int, 4> markerStyles = {{20, 21, 22, 23}};

struct TableData {
    std::vector<double> momentum;
    std::array<std::vector<double>, 4> tof;
    std::array<double, 4> mass = {};
    double length = 0;
    double speedOfLight = 0;
};

inline std::string Join(const std::string& directory, const std::string& name) {
    return directory + "/" + name;
}

inline double Number(const std::string& token) {
    std::size_t end = 0;
    const double value = std::stod(token, &end);
    if (end != token.size() || !std::isfinite(value))
        throw std::runtime_error("Invalid numeric field: " + token);
    return value;
}

// Read the existing tables and check them against their recorded physics parameters.
inline TableData ReadTables(const std::string& directory, const std::string& prefix) {
    const std::string filename = Join(directory, prefix + "_tof.csv");
    std::ifstream input(filename);
    if (!input) throw std::runtime_error("Cannot read " + filename);
    std::string line;
    std::getline(input, line);
    if (!line.empty() && line.back() == '\r') line.pop_back();
    if (line != "momentum_GeV_c,path_length_m,electron_tof_ns,pion_tof_ns,kaon_tof_ns,proton_tof_ns")
        throw std::runtime_error("Unexpected CSV header: " + filename);
    TableData data;
    while (std::getline(input, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty()) continue;
        std::stringstream stream(line);
        std::vector<double> values;
        std::string field;
        while (std::getline(stream, field, ',')) values.push_back(Number(field));
        if (values.size() != 6 || line.back() == ',')
            throw std::runtime_error("Expected six columns in " + filename);
        if (values[0] <= 0 || (!data.momentum.empty() && values[0] <= data.momentum.back()))
            throw std::runtime_error("Momentum must be positive and increasing");
        if (data.momentum.empty()) data.length = values[1];
        if (data.length <= 0 || std::abs(values[1] - data.length) > 1e-10)
            throw std::runtime_error("Expected one positive flight-path length");
        data.momentum.push_back(values[0]);
        for (unsigned i = 0; i < 4; ++i) data.tof[i].push_back(values[i + 2]);
    }
    if (data.momentum.size() < 2) throw std::runtime_error("At least two momentum rows are required");

    double maximumDifference = 0;
    for (unsigned i = 0; i < 4; ++i) {
        const std::string metadataFile = Join(directory, prefix + "_" + particles[i] + "_tof.txt");
        std::ifstream metadata(metadataFile);
        if (!metadata) throw std::runtime_error("Cannot read " + metadataFile);
        double mass = -1, length = -1, c = -1;
        while (std::getline(metadata, line)) {
            if (line.find("# Mass: ") == 0) {
                mass = std::stod(line.substr(8));
                const auto position = line.find("path length: ");
                if (position != std::string::npos) length = std::stod(line.substr(position + 13));
            }
            if (line.find("# TOF = ") == 0) {
                const auto position = line.rfind("c = ");
                if (position != std::string::npos) c = std::stod(line.substr(position + 4));
            }
        }
        if (!std::isfinite(mass) || mass < 0 || !std::isfinite(c) || c <= 0 ||
            !std::isfinite(length) || std::abs(length - data.length) > 1e-10)
            throw std::runtime_error("Missing or inconsistent metadata: " + metadataFile);
        if (i == 0) data.speedOfLight = c;
        if (std::abs(c - data.speedOfLight) > 1e-12)
            throw std::runtime_error("Inconsistent speed of light in " + metadataFile);
        data.mass[i] = mass;
        for (unsigned j = 0; j < data.momentum.size(); ++j) {
            const double expected = data.length / c * std::hypot(1.0, mass / data.momentum[j]);
            const double difference = std::abs(expected - data.tof[i][j]);
            maximumDifference = std::max(maximumDifference, difference);
            if (difference > 5.1e-7)
                throw std::runtime_error("TOF disagrees with metadata: " + metadataFile);
        }
    }
    std::cout << "Validated " << filename << ": " << data.momentum.size()
              << " rows, L = " << data.length << " m; maximum curve/table difference = "
              << maximumDifference << " ns" << std::endl;
    return data;
}

// Split sampled functions into visible dashes with continuous screen-space spacing.
inline void DrawDashedCurve(const TF1& function, unsigned particle, double xScale,
                            double yScale, std::vector<std::unique_ptr<TGraph>>& strokes) {
    const double dash = dashPixels[particle], gap = gapPixels[particle];
    bool visible = true;
    double remaining = dash;
    std::vector<double> xs, ys;
    auto flush = [&]() {
        if (xs.size() > 1) {
            std::unique_ptr<TGraph> stroke(new TGraph(xs.size(), xs.data(), ys.data()));
            stroke->SetLineColor(function.GetLineColor());
            stroke->SetLineWidth(function.GetLineWidth());
            stroke->SetLineStyle(1);
            stroke->Draw("L SAME");
            strokes.push_back(std::move(stroke));
        }
        xs.clear();
        ys.clear();
    };
    double x = function.GetXmin(), y = function.Eval(x);
    xs.push_back(x);
    ys.push_back(y);
    for (int step = 1; step <= function.GetNpx(); ++step) {
        const double endX = function.GetXmin() +
            (function.GetXmax() - function.GetXmin()) * step / function.GetNpx();
        const double endY = function.Eval(endX);
        double distance = std::hypot((endX - x) * xScale, (endY - y) * yScale);
        while (distance > 1e-10) {
            const double advance = std::min(remaining, distance);
            const double fraction = advance / distance;
            x += fraction * (endX - x);
            y += fraction * (endY - y);
            if (visible) {
                xs.push_back(x);
                ys.push_back(y);
            }
            distance -= advance;
            remaining -= advance;
            if (remaining < 1e-10) {
                if (visible) flush();
                visible = !visible;
                remaining = visible ? dash : gap;
                if (visible) {
                    xs.push_back(x);
                    ys.push_back(y);
                }
            }
        }
        x = endX;
        y = endY;
    }
    flush();
}

// Draw one particle or all particles; save raster PNG and vector PDF.
inline void DrawPlot(const TableData& data, const std::string& spectrometer,
                     const std::string& prefix, const std::vector<unsigned>& selected,
                     const std::string& outputDirectory) {
    const bool combined = selected.size() > 1;
    const std::string tag = combined ? "all" : particles[selected.front()];
    const std::string stem = prefix + "_tof_vs_momentum_" + tag;
    double minimum = data.tof[selected.front()].front(), maximum = minimum;
    for (unsigned i : selected) {
        minimum = std::min(minimum, *std::min_element(data.tof[i].begin(), data.tof[i].end()));
        maximum = std::max(maximum, *std::max_element(data.tof[i].begin(), data.tof[i].end()));
    }
    const double span = maximum - minimum;
    double lower = minimum - 0.07 * span, upper = maximum + 0.10 * span;
    if (span < 0.2) {
        const double center = (minimum + maximum) / 2;
        lower = center - 0.1;
        upper = center + 0.1;
    }

    if (combined && spectrometer == "SHMS") lower = 55.0;

    TCanvas canvas(stem.c_str(), stem.c_str(), 1800, 1350);
    canvas.SetCanvasSize(1800, 1350);
    canvas.SetFillColor(kWhite);
    canvas.SetFrameFillColor(kWhite);
    canvas.SetBorderMode(0);
    canvas.SetFrameBorderMode(0);
    canvas.SetLeftMargin(0.14);
    canvas.SetRightMargin(0.04);
    canvas.SetTopMargin(0.13);
    canvas.SetBottomMargin(0.15);
    canvas.SetTicks(1, combined ? 0 : 1);
    canvas.SetLogy(false);
    TH1F* frame = canvas.DrawFrame(0.0, lower, 11.5, upper);
    frame->SetTitle("");
    frame->SetStats(false);
    frame->GetXaxis()->SetTitle("p(GeV/c)");
    frame->GetYaxis()->SetTitle("TOF(ns)");
    for (TAxis* axis : {frame->GetXaxis(), frame->GetYaxis()}) {
        axis->SetTitleFont(132);
        axis->SetLabelFont(132);
        axis->SetTitleSize(0.048);
        axis->CenterTitle();
        axis->SetLabelSize(0.043);
        axis->SetLabelOffset(0.012);
        axis->SetNdivisions(505);
    }
    frame->GetXaxis()->SetNdivisions(510);
    if (combined && spectrometer == "SHMS") frame->GetYaxis()->SetNdivisions(510);
    frame->GetXaxis()->SetTitleOffset(1.05);
    frame->GetYaxis()->SetTitleOffset(1.25);

    TLegend legend(0.67, 0.60, 0.93, 0.83);
    legend.SetBorderSize(0);
    legend.SetFillStyle(0);
    legend.SetTextFont(132);
    legend.SetTextSize(0.042);
    // Only combined plots use two blocks with independent vertical ranges.
    const double splitMomentum = 2.0;
    const double xMin = frame->GetXaxis()->GetXmin();
    const double xMax = frame->GetXaxis()->GetXmax();
    const double frameLeft = canvas.GetLeftMargin();
    const double frameRight = 1 - canvas.GetRightMargin();
    const double frameBottom = canvas.GetBottomMargin();
    const double frameTop = 1 - canvas.GetTopMargin();
    const double splitPosition = frameLeft + (frameRight - frameLeft) *
        (splitMomentum - xMin) / (xMax - xMin);
    const double rightLower = spectrometer == "SHMS" ? 55.0 : 70.0;
    const double rightUpper = spectrometer == "SHMS" ? 70.0 : 80.0;
    const double xScale = canvas.GetWw() * (frameRight - frameLeft) / (xMax - xMin);
    std::array<std::unique_ptr<TPad>, 2> blocks;
    std::vector<std::unique_ptr<TGraph>> strokes;
    std::vector<std::unique_ptr<TF1>> curves;
    std::vector<std::unique_ptr<TGraph>> points;
    const unsigned blockCount = combined ? 2 : 1;
    for (unsigned block = 0; block < blockCount; ++block) {
        const double blockXMin = block == 0 ? xMin : splitMomentum;
        const double blockXMax = combined && block == 0 ? splitMomentum : xMax;
        const double blockLower = block == 0 ? lower : rightLower;
        const double blockUpper = block == 0 ? upper : rightUpper;
        canvas.cd();
        blocks[block].reset(new TPad((stem + "_block_" + std::to_string(block)).c_str(), "",
            block == 0 ? frameLeft : splitPosition, frameBottom,
            combined && block == 0 ? splitPosition : frameRight, frameTop));
        TPad& pad = *blocks[block];
        pad.SetMargin(0, 0, 0, 0);
        pad.SetBorderMode(0);
        pad.SetFrameBorderMode(0);
        pad.SetFillColor(kWhite);
        pad.Draw();
        pad.cd();
        TH1F* blockFrame = pad.DrawFrame(blockXMin, blockLower, blockXMax, blockUpper);
        for (TAxis* axis : {blockFrame->GetXaxis(), blockFrame->GetYaxis()}) {
            axis->SetLabelSize(0);
            axis->SetTickLength(0);
        }
        const double yScale = canvas.GetWh() * (frameTop - frameBottom) /
            (blockUpper - blockLower);
        for (unsigned i : selected) {
            const int color = TColor::GetColor(colors[i]);
            std::unique_ptr<TF1> curve(new TF1((stem + "_" + particles[i] +
                "_block_" + std::to_string(block)).c_str(), "[0]/[1]*sqrt(1+([2]/x)^2)",
                std::max(blockXMin, data.momentum.front()),
                std::min(blockXMax, data.momentum.back())));
            curve->SetParameters(data.length, data.speedOfLight, data.mass[i]);
            curve->SetNpx(2000);
            curve->SetLineColor(color);
            curve->SetLineWidth(2);
            curve->SetLineStyle(lineStyles[i]);
            if (lineStyles[i] == 1) curve->Draw("SAME");
            else DrawDashedCurve(*curve, i, xScale, yScale, strokes);
            std::vector<double> momenta, times;
            for (unsigned row = 0; row < data.momentum.size(); ++row) {
                if (data.momentum[row] < blockXMin || data.momentum[row] > blockXMax) continue;
                if (data.tof[i][row] < blockLower || data.tof[i][row] > blockUpper) continue;
                momenta.push_back(data.momentum[row]);
                times.push_back(data.tof[i][row]);
            }
            std::unique_ptr<TGraph> graph(new TGraph(momenta.size(), momenta.data(), times.data()));
            graph->SetMarkerColor(color);
            graph->SetMarkerStyle(markerStyles[i]);
            graph->SetMarkerSize(markerSize);
            graph->SetLineColor(color);
            graph->SetLineWidth(2);
            graph->SetLineStyle(lineStyles[i]);
            if (!momenta.empty()) graph->Draw("P SAME");
            if (block == 0) legend.AddEntry(graph.get(), labels[i], "lp");
            curves.push_back(std::move(curve));
            points.push_back(std::move(graph));
        }
        pad.Modified();
        pad.Update();
    }
    canvas.cd();
    canvas.RedrawAxis();
    TLine divider(splitMomentum, lower, splitMomentum, upper);
    divider.SetLineColor(kGray + 1);
    if (combined) divider.Draw();
    TGaxis rightAxis(xMax, lower, xMax, upper, rightLower, rightUpper, spectrometer == "SHMS" ? 503 : 505, "+LN");
    rightAxis.SetLabelFont(132);
    rightAxis.SetLabelSize(0.037);
    rightAxis.SetLabelOffset(0.008);
    rightAxis.SetTickSize(0.012);
    if (combined) rightAxis.Draw();
    if (combined) legend.Draw();
    TLatex text;
    text.SetNDC();
    text.SetTextFont(132);
    if (combined && spectrometer == "SHMS") {
        text.SetTextSize(0.043);
        text.SetTextAlign(32);
        text.DrawLatex(frameLeft - 0.012, frameBottom, Form("%g", lower));
    }
    text.SetTextSize(0.024);
    text.SetTextAlign(21);
    if (combined) text.DrawLatex(splitPosition, 0.88, "2 GeV/c");
    text.SetTextAlign(11);
    text.SetTextSize(0.046);
    text.DrawLatex(0.14, 0.925, Form("#bf{%s}   L = %.6g m", spectrometer.c_str(), data.length));
    text.SetTextAlign(31);
    text.DrawLatex(0.96, 0.925, combined ? "All particles" : labels[selected.front()]);
    text.SetTextAlign(11);
    text.SetTextSize(0.024);
    text.DrawLatex(0.14, 0.015, "Target to focal-plane center; central trajectory, no energy loss");
    canvas.Modified();
    canvas.Update();
    for (const char* extension : {"png", "pdf"}) {
        const std::string filename = Join(outputDirectory, stem + "." + extension);
        canvas.SaveAs(filename.c_str());
        std::ifstream saved(filename, std::ios::binary | std::ios::ate);
        if (!saved || saved.tellg() <= 0) throw std::runtime_error("Failed to write " + filename);
    }
    std::cout << "Saved " << stem << ".png/.pdf" << std::endl;
}

inline void Plot(const std::string& spectrometer, const std::string& prefix,
                 const char* macroFile, const char* inputDirectory, const char* outputDirectory) {
    const std::string base = gSystem->DirName(macroFile);
    const std::string input = inputDirectory[0] ? inputDirectory : Join(base, "tables/" + spectrometer);
    const std::string output = outputDirectory[0] ? outputDirectory : Join(base, "plots/" + spectrometer);
    const TableData data = ReadTables(input, prefix);
    if (gSystem->AccessPathName(output.c_str()) && gSystem->mkdir(output.c_str(), true) != 0)
        throw std::runtime_error("Cannot create output directory: " + output);
    for (unsigned i = 0; i < 4; ++i) DrawPlot(data, spectrometer, prefix, {i}, output);
    DrawPlot(data, spectrometer, prefix, {0, 1, 2, 3}, output);
}

} // namespace HallCTOF
#endif
