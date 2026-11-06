# GPU Reduction

**When does moving data cost more than computing on it?**

An independent C++17/CUDA reduction study: sum float32 arrays using float64
accumulation, verify every result, and measure GPU-resident work separately from
host-to-device transfer plus execution. A single-thread CPU implementation provides
a runnable reference and a clearly bounded comparison.

**Validation status:** CPU checks passed on Mac and Linux. On an EIDF NVIDIA A100
40 GB, the CUDA correctness suite, all four Compute Sanitizer tools and repeated
CPU/GPU benchmark reproduction passed. See [validation](docs/validation.md) and
[recorded measurements](results/a100-validation.json) for the exact tested source
and limitations. GitHub CI has been prepared but has not run for this project.

## Run the CPU reference

Requires a C++17 compiler, Make and Python 3.9+; no Python packages required.

```sh
make CXX=c++ test
./build/reduce_cpu 65537 cancellation 5
python3 scripts/benchmark.py results/local-example --backend cpu
```

On the author's Mac, use `CXX=/usr/bin/clang++` if an unrelated compiler earlier
on PATH has a different architecture. CPU tests do not require CUDA.

The example must report `"expected":100032768`, `"validation":"pass"` and five
samples with `"sum":100032768`. Timings vary; tiny cases may measure zero clock ticks.

## Build and validate on NVIDIA hardware

Requires a compatible NVIDIA GPU/driver and CUDA Toolkit with `nvcc` and
`compute-sanitizer`. The default build target is `sm_70`, tested with CUDA 12.0. CUDA 13.0 no longer
lists that target; `sm_80` was compiled successfully with it. Select an architecture
supported by both the device and installed compiler. See the tested commands in
[validation](docs/validation.md).

```sh
make clean
make CXX=g++ cuda CUDA_ARCH=sm_70
make CXX=g++ test
make test-cuda CUDA_ARCH=sm_70
make gpu-sanitize CUDA_ARCH=sm_70
python3 scripts/benchmark.py results/local-gpu-example --backend both --repeats 5
```

These commands **fail** if the CUDA compiler, device or sanitizer is unavailable;
there is no automatic CPU fallback. Change `CUDA_ARCH` for the actual device and
clean-rebuild after changing any compiler/flags/architecture. Automatic GPU cluster
submission and privileged self-hosted GitHub runners are intentionally absent.

## Input and result contract

- CPU: `reduce_cpu N PATTERN REPEATS`
- CUDA: `reduce_cuda N PATTERN REPEATS [THREADS]`
- `N`: 1–16,777,216; `REPEATS`: 1–100.
- Patterns: `ones`, `alternating`, `ramp`, `cancellation`.
- CUDA block size: 64, 128, 256 or 512; default 256.

Every run prints one JSON record with configuration, analytical expectation,
validation status, raw samples and backend/device metadata. Errors go to stderr
and produce a nonzero exit. Inputs are generated deterministically; no downloaded
dataset or random seed is needed. See [numerical contract](docs/numerics.md).

## How the GPU path works

```mermaid
flowchart LR
    H[Host float32 array] -->|Upload| D[Device input]
    D --> B[Grid-stride loading and float64 block sums]
    B --> R[Reduce partial sums in disjoint scratch buffers]
    R -->|Download one float64 scalar| V[Independent analytical check]
```

Every thread participates in block synchronization, including threads beyond the
array tail. Up to 1,024 blocks write separate partial sums; subsequent passes
reduce them to one scalar. The original device input stays intact for repetitions.

## What the timings mean

| Measurement | Includes | Excludes |
|---|---|---|
| CPU | Single-thread reduction, host steady clock | Generation, allocation, validation |
| CUDA resident | All reduction passes, CUDA event interval | Upload and scalar download |
| CUDA with transfers | Pageable-host upload, reduction, blocking scalar download | Context/buffer setup, input generation, validation |

Both paths warm up before repeated measurements. This is an educational custom
kernel, not a claim to beat CUB or a tuned multithread CPU reduction. Float64
throughput varies by GPU. The recorded A100 measurements are a bounded first run, not evidence of peak
bandwidth or a general speedup; bottleneck attribution still needs profiling. See [measurement protocol](docs/benchmarking.md).

Benchmark folders must be new. They preserve raw stdout/stderr, validation logs,
compiler commands, source/binary hashes and min/median/max timings. A failed or
interrupted run never becomes a successful report. The CPU GitHub workflow, once
run, proves only its named CPU checks.

## Provenance and license

[MIT licensed](LICENSE). This project was written separately from the university
coursework. No archived source, assessment solutions, reports or historical GPU
measurements were copied. Original archives remain private and unchanged.
See [provenance](docs/provenance.md) and [contribution guidance](CONTRIBUTING.md).
