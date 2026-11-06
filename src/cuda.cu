#include "reduction.hpp"
#include <cuda_runtime.h>
#include <algorithm>
#include <chrono>
#include <stdexcept>

namespace {
void check(cudaError_t status, const char* operation) {
    if (status != cudaSuccess)
        throw std::runtime_error(std::string(operation) + ": " + cudaGetErrorString(status));
}
template<class T> struct Buffer {
    T* data = nullptr;
    explicit Buffer(std::size_t n) {
        check(cudaMalloc(reinterpret_cast<void**>(&data), n * sizeof(T)), "cudaMalloc");
    }
    ~Buffer() { if (data) cudaFree(data); }
    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;
};
struct Event {
    cudaEvent_t value = nullptr;
    Event() { check(cudaEventCreate(&value), "cudaEventCreate"); }
    ~Event() { if (value) cudaEventDestroy(value); }
    Event(const Event&) = delete;
    Event& operator=(const Event&) = delete;
};

template<class T> __global__ void block_reduce(const T* input, double* output, std::size_t n) {
    extern __shared__ double shared[];
    const unsigned tid = threadIdx.x;
    const std::size_t stride = static_cast<std::size_t>(blockDim.x) * gridDim.x;
    double local = 0;
    for (std::size_t i = static_cast<std::size_t>(blockIdx.x) * blockDim.x + tid;
         i < n; i += stride) local += static_cast<double>(input[i]);
    shared[tid] = local;
    __syncthreads();
    for (unsigned offset = blockDim.x / 2; offset > 0; offset /= 2) {
        if (tid < offset) shared[tid] += shared[tid + offset];
        __syncthreads();
    }
    if (tid == 0) output[blockIdx.x] = shared[0];
}

unsigned blocks_for(std::size_t n, unsigned threads) {
    return static_cast<unsigned>(std::min<std::size_t>(1024, (n + threads - 1) / threads));
}
double* launch(const float* input, std::size_t n, unsigned threads, double* a, double* b) {
    unsigned blocks = blocks_for(n, threads);
    block_reduce<<<blocks, threads, threads * sizeof(double)>>>(input, a, n);
    check(cudaGetLastError(), "float reduction launch");
    double* current = a;
    double* next = b;
    while (blocks > 1) {
        const unsigned count = blocks;
        blocks = blocks_for(count, threads);
        block_reduce<<<blocks, threads, threads * sizeof(double)>>>(current, next, count);
        check(cudaGetLastError(), "partial reduction launch");
        std::swap(current, next);
    }
    return current;
}
}

Measurement run_backend(const std::vector<float>& input, const Config& config) {
    int count = 0;
    check(cudaGetDeviceCount(&count), "cudaGetDeviceCount (real NVIDIA GPU required)");
    if (count < 1) throw std::runtime_error("No CUDA device; GPU validation was not run");
    check(cudaSetDevice(0), "cudaSetDevice");
    cudaDeviceProp properties{};
    check(cudaGetDeviceProperties(&properties, 0), "cudaGetDeviceProperties");
    if (config.threads > static_cast<unsigned>(properties.maxThreadsPerBlock))
        throw std::runtime_error("Thread count exceeds device capability");
    Measurement measurement;
    measurement.device = properties.name;
    measurement.compute_major = properties.major;
    measurement.compute_minor = properties.minor;
    check(cudaRuntimeGetVersion(&measurement.runtime_version), "cudaRuntimeGetVersion");
    check(cudaDriverGetVersion(&measurement.driver_version), "cudaDriverGetVersion");
    measurement.samples.reserve(config.repeats);
    Buffer<float> device_input(input.size());
    Buffer<double> scratch_a(1024), scratch_b(1024);
    Event start, stop;
    const double expected = expected_sum(config);
    const std::size_t bytes = input.size() * sizeof(float);
    auto transfer = [&]() {
        check(cudaMemcpy(device_input.data, input.data(), bytes, cudaMemcpyHostToDevice), "input upload");
    };
    auto reduce = [&]() { return launch(device_input.data, input.size(), config.threads, scratch_a.data, scratch_b.data); };
    auto download = [&](const double* result) {
        double host = 0;
        check(cudaMemcpy(&host, result, sizeof(double), cudaMemcpyDeviceToHost), "result download/synchronize");
        return host;
    };
    // Warm each path, including compilation/context and first-use effects.
    transfer();
    validate_sum(download(reduce()), expected);
    transfer();
    validate_sum(download(reduce()), expected);
    for (unsigned i = 0; i < config.repeats; ++i) {
        Sample sample;
        check(cudaEventRecord(start.value), "record start");
        const double* result = reduce();
        check(cudaEventRecord(stop.value), "record stop");
        check(cudaEventSynchronize(stop.value), "synchronize reduction");
        float milliseconds = 0;
        check(cudaEventElapsedTime(&milliseconds, start.value, stop.value), "elapsed reduction time");
        sample.resident_seconds = static_cast<double>(milliseconds) * 0.001;
        sample.sum = download(result);
        validate_sum(sample.sum, expected);
        const auto begin = std::chrono::steady_clock::now();
        transfer();
        sample.transfer_sum = download(reduce());
        const auto end = std::chrono::steady_clock::now();
        sample.transfer_seconds = std::chrono::duration<double>(end - begin).count();
        validate_sum(sample.transfer_sum, expected);
        measurement.samples.push_back(sample);
    }
    check(cudaDeviceSynchronize(), "final device synchronization");
    return measurement;
}
