#pragma once
#include <cstddef>
#include <string>
#include <vector>

struct Config {
    std::size_t n;
    std::string pattern;
    unsigned repeats;
    unsigned threads;
};
struct Sample {
    double sum = 0;
    double cpu_seconds = 0;
    double resident_seconds = 0;
    double transfer_seconds = 0;
    double transfer_sum = 0;
};
struct Measurement {
    std::string device;
    int runtime_version = 0;
    int driver_version = 0;
    int compute_major = 0;
    int compute_minor = 0;
    std::vector<Sample> samples;
};

std::vector<float> make_input(const Config& config);
double expected_sum(const Config& config);
void validate_sum(double actual, double expected);
Measurement run_backend(const std::vector<float>& input, const Config& config);
