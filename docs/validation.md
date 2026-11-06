# Validation status

Observed 6 November 2026. CPU validation passed on Mac and Linux. CUDA compilation
passed with two VM toolchains; the full GPU validation then passed on an EIDF
NVIDIA A100-SXM4-40GB using CUDA 13.0.48. GPU access was restored by loading the
VM's existing login-shell configuration, without changing the credentials.

| Check | Status | Evidence and limit |
|---|---|---|
| Independent implementation | PASS | No recovered coursework source or results copied; separate project directory |
| Strict CPU build | PASS on Mac and Linux | Apple clang 21 and GNU C++ 12; C++17, warnings treated as errors |
| CPU contract and evidence tests | PASS on Mac and Linux | 10 unittest methods; includes many numerical/input configurations |
| CPU AddressSanitizer/UBSan | PASS on Mac and Linux | All four executable-contract test methods under instrumentation |
| CPU benchmark reproduction | PASS on Mac and Linux | Three sizes, five raw repetitions each; exact analytical validation |
| Independent static review | PASS after fixes | No observed numerical/indexing blocker; two provenance findings reproduced and corrected |
| Clean-directory CPU build | PASS locally | No installed project package or archived files are required |
| CUDA compilation | PASS on EIDF VM | CUDA 12.0.140 / sm_70 / g++-12 and CUDA 13.0.88 / sm_80 |
| CUDA numerical tests | PASS on A100 | Four test methods; all patterns, block sizes, partial blocks and grid-stride cases |
| Compute Sanitizer | PASS on A100 | memcheck, racecheck, initcheck, synccheck; three cases each, zero reported errors/hazards |
| GPU benchmark reproduction | PASS for recorded run | Three sizes, five repeats per backend; resident and transfer-inclusive timings; no peak-performance claim |
| GitHub CPU workflow | PREPARED, NOT RUN | No GPU repository has been uploaded or published |
| Public release | NOT PUBLISHED | Hardware gates passed for tested source; GitHub CI and exact publication review remain |

Local raw artifacts belong under ignored `results/local-*`. Each benchmark report
records source/script/test hashes, build manifests and whether its Git working tree
was clean. Machine-readable status is in `results/validation-summary.json`.
The initial local benchmark predates the first commit and correctly records no
commit rather than attributing measurements to an unrelated parent repository.

## Review findings resolved

1. Git can discover an enclosing repository. The benchmark now accepts Git
   metadata only when the discovered repository root is exactly this project.
   A temporary nested-project regression test catches this case.
2. Source hashing and Make dependencies originally disagreed, and missing build
   manifests were not repaired. Build targets now always regenerate the executable
   and manifest together. A regression test edits a source, rebuilds and validates
   the recorded hash, then deletes the manifest and verifies regeneration.

The numerical suite deliberately requires a backend-specific executable and checks
its reported backend. GPU targets do not pass through fallback, skipped tests or
historical coursework results. Stronger general-purpose floating-point or tuned
library performance claims are outside the current numerical contract.

## EIDF compilation and Linux evidence

Tested source commit: `71a3fe79eb34ffaf80ebd0918db80813a798fcaa`.
Transferred archive SHA-256:
`01ecb9b28347a7ccdcdccf2a9d2c36b9ab22b3bf24275522dd5e3a685099f75d`.
The source-only archive was extracted into a new, uniquely named directory under
the owner's VM home. It contains no coursework. Original directories, drivers,
Kubernetes configuration and billing settings were not changed. This first VM-only
stage did not submit a cluster job; the subsequent GPU run is recorded below.

Verified commands on the existing Ubuntu VM:

```sh
make CXX=g++-12 test
make CXX=g++-12 sanitize
make NVCC=/usr/bin/nvcc NVCCFLAGS='-O3 -std=c++17 -lineinfo -ccbin=g++-12' cuda
make NVCC=/usr/local/cuda-13.0/bin/nvcc CUDA_ARCH=sm_80 cuda
python3 scripts/benchmark.py NEW_RESULTS_DIRECTORY --backend cpu --repeats 5
```

CUDA 12 uses the installed compatible GNU C++ 12 explicitly; neither compiler was
installed or upgraded for this check. CUDA 13 was compiled for sm_80; this does not
establish that a compatible GPU is currently allocated. The device probe used the
CUDA 12 executable and failed before any kernel execution. The CUDA 13 executable
was compiled only.

Downloaded logs, build manifests and raw CPU measurements are saved privately in
`results/eidf-2026-11-06-71a3fe7/`. The transferred archive checksum matched before
extraction. Every source hash in both CUDA manifests and the CPU manifest, plus
the benchmark source/script/test hashes, matches the local project. Subsequent
status-document edits do not change these implementation files. Benchmark Git
metadata is null on the source-only VM copy; the verified archive and this explicit
source commit provide its provenance instead of inventing a remote Git history.

## GPU access diagnosis and completed run

The early non-interactive SSH probe did not load the login environment. It found
no default kubeconfig and incorrectly inferred that the GPU-service configuration
was missing. The existing file is `/kubernetes/config`; a login shell sets
`KUBECONFIG` to this path. Its context and project access were verified live.
No credentials were copied, displayed, edited or committed.

A single job used one A100 GPU, two CPU cores and 2 GiB RAM within the existing
project quota. It had a 900-second hard deadline, no retries, no service-account
token mount, and only a source archive plus a validation script as input. The job
completed with exit code zero. The source archive checksum, code fingerprints,
all test logs, sanitizer summaries and raw benchmark sums were checked after
retrieval. No original coursework was uploaded or changed.

| GPU-stage check | Observed result |
|---|---|
| CPU integration/evidence suite | 10 methods passed |
| CPU AddressSanitizer/UBSan contract suite | 4 methods passed |
| CUDA contract suite | 4 methods passed; 58.358 seconds |
| Compute Sanitizer | Four tools x three cases at 256 threads; zero reported errors/hazards |
| Benchmarks | CPU and CUDA, 3 lengths, 5 repeats each; every sum validated |

GPU: NVIDIA A100-SXM4-40GB, compute capability 8.0, driver 570.124.06.
Container toolchain: nvcc 13.0.48, GNU C++ 13.3.0, Python 3.12.3, target sm_80.
The immutable container image identity and completed job record are retained with
the private raw evidence. This describes an observed working environment, not a
promise that every CUDA 13/driver combination is supported.

Public-safe raw samples and source hashes: [a100-validation.json](../results/a100-validation.json).
Full private artifacts: `results/eidf-gpu-2026-11-06-71a3fe7/`.
Host CPU model and clock/contention controls were not captured; do not turn these
measurements into hardware-independent speedup claims. The project remains local;
GitHub workflow checks have not yet been run.

After verified retrieval, the temporary job, its pod and its source ConfigMap were
removed. The original VM configuration and all other workloads were left unchanged.
