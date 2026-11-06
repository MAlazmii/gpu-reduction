#include "reduction.hpp"
#include <chrono>

namespace {
double reduce(const std::vector<float>& input) {
    double result = 0;
    for (float value : input) result += static_cast<double>(value);
    return result;
}
}
Measurement run_backend(const std::vector<float>& input, const Config& config) {
    Measurement measurement;
    measurement.device = "single CPU thread";
    measurement.samples.reserve(config.repeats);
    const double expected = expected_sum(config);
    validate_sum(reduce(input), expected);
    for (unsigned i = 0; i < config.repeats; ++i) {
        const auto begin = std::chrono::steady_clock::now();
        const double result = reduce(input);
        const auto end = std::chrono::steady_clock::now();
        validate_sum(result, expected);
        Sample sample;
        sample.sum = result;
        sample.cpu_seconds = std::chrono::duration<double>(end - begin).count();
        measurement.samples.push_back(sample);
    }
    return measurement;
}
