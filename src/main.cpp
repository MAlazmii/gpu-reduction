#include "reduction.hpp"
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>

namespace {
std::size_t integer(const char* text, std::size_t maximum) {
    const std::string value(text);
    if (value.empty()) throw std::invalid_argument("Empty integer");
    std::size_t result = 0;
    for (const char c : value) {
        if (c < '0' || c > '9') throw std::invalid_argument("Expected unsigned decimal integer");
        const auto digit = static_cast<std::size_t>(c - '0');
        if (result > (maximum - digit) / 10) throw std::invalid_argument("Integer exceeds supported bound");
        result = result * 10 + digit;
    }
    if (result == 0 || result > maximum) throw std::invalid_argument("Integer outside supported range");
    return result;
}
std::string quote(const std::string& input) {
    std::string result = "\"";
    constexpr char hex[] = "0123456789abcdef";
    for (const char raw : input) {
        const auto c = static_cast<unsigned char>(raw);
        if (c == '"' || c == '\\') { result += '\\'; result += raw; }
        else if (c < 32) { result += "\\u00"; result += hex[c / 16]; result += hex[c % 16]; }
        else result += raw;
    }
    return result + '"';
}
}

std::vector<float> make_input(const Config& config) {
    std::vector<float> input(config.n);
    constexpr float cancellation[] = {100000000.0F, 1.0F, -100000000.0F, 1.0F};
    for (std::size_t i = 0; i < input.size(); ++i) {
        if (config.pattern == "ones") input[i] = 1.0F;
        else if (config.pattern == "alternating") input[i] = i % 2 == 0 ? 1.0F : -1.0F;
        else if (config.pattern == "ramp") input[i] = static_cast<float>(static_cast<int>(i % 1024) - 512) / 512.0F;
        else input[i] = cancellation[i % 4];
    }
    return input;
}

double expected_sum(const Config& config) {
    if (config.pattern == "ones") return static_cast<double>(config.n);
    if (config.pattern == "alternating") return static_cast<double>(config.n % 2);
    if (config.pattern == "ramp") {
        const double tail = static_cast<double>(config.n % 1024);
        return -static_cast<double>(config.n / 1024) + (tail * (tail - 1) / 2 - 512 * tail) / 512;
    }
    constexpr double tails[] = {0, 100000000, 100000001, 1};
    return 2 * static_cast<double>(config.n / 4) + tails[config.n % 4];
}

void validate_sum(double actual, double expected) {
    if (!std::isfinite(actual) || actual != expected)
        throw std::runtime_error("Numerical validation failed: result differs from analytical sum");
}

int main(int argc, char** argv) {
    try {
#ifdef REDUCE_CUDA
        constexpr bool cuda = true;
#else
        constexpr bool cuda = false;
#endif
        if (argc != 4 && !(cuda && argc == 5))
            throw std::invalid_argument("Usage: reduce_cpu N PATTERN REPEATS; reduce_cuda N PATTERN REPEATS [THREADS]");
        Config config{integer(argv[1], 16777216), argv[2],
                      static_cast<unsigned>(integer(argv[3], 100)), 256};
        if (config.pattern != "ones" && config.pattern != "alternating" &&
            config.pattern != "ramp" && config.pattern != "cancellation")
            throw std::invalid_argument("PATTERN must be ones, alternating, ramp or cancellation");
        if (argc == 5) config.threads = static_cast<unsigned>(integer(argv[4], 512));
        if (config.threads != 64 && config.threads != 128 && config.threads != 256 && config.threads != 512)
            throw std::invalid_argument("THREADS must be 64, 128, 256 or 512");
        const auto input = make_input(config);
        const double expected = expected_sum(config);
        const auto measurement = run_backend(input, config);
        if (measurement.samples.size() != config.repeats) throw std::runtime_error("Incomplete measurement");
        for (const auto& sample : measurement.samples) {
            validate_sum(sample.sum, expected);
            if (cuda) validate_sum(sample.transfer_sum, expected);
        }
        std::cout << std::setprecision(std::numeric_limits<double>::max_digits10)
                  << "{\"schema_version\":1,\"backend\":" << quote(cuda ? "cuda" : "cpu")
                  << ",\"n\":" << config.n << ",\"pattern\":" << quote(config.pattern)
                  << ",\"precision\":\"float32 input / float64 accumulation\",\"threads\":";
        if (cuda) std::cout << config.threads; else std::cout << "null";
        std::cout << ",\"expected\":" << expected << ",\"validation\":\"pass\",\"device\":" << quote(measurement.device)
                  << ",\"runtime_version\":" << measurement.runtime_version
                  << ",\"driver_version\":" << measurement.driver_version
                  << ",\"compute_capability\":" << quote(std::to_string(measurement.compute_major) + "." + std::to_string(measurement.compute_minor))
                  << ",\"warmups_per_path\":1,\"samples\":[";
        bool first = true;
        for (const auto& sample : measurement.samples) {
            if (!first) std::cout << ',';
            first = false;
            std::cout << "{\"sum\":" << sample.sum;
            if (cuda) std::cout << ",\"transfer_sum\":" << sample.transfer_sum
                               << ",\"resident_seconds\":" << sample.resident_seconds
                               << ",\"transfer_seconds\":" << sample.transfer_seconds;
            else std::cout << ",\"cpu_seconds\":" << sample.cpu_seconds;
            std::cout << '}';
        }
        std::cout << "]}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << '\n';
        return 1;
    }
}
