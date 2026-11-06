# Validation status

Observed 6 November 2026. CPU validation passed on Mac and the existing EIDF VM.
CUDA compilation passed with two installed toolchains. The VM has no visible NVIDIA
device, and its user's Kubernetes configuration has no current context. An actual
CUDA probe exited nonzero with "no CUDA-capable device is detected". GPU numerical
checks, Compute Sanitizer and GPU benchmarks remain **NOT RUN**, not passed.

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
| CUDA numerical tests | NOT RUN | Requires approved real NVIDIA GPU access |
| Compute Sanitizer | NOT RUN | memcheck, racecheck, initcheck, synccheck must all pass |
| GPU performance | NOT RUN | No GPU timings, speedup, bandwidth or optimization claim |
| GitHub CPU workflow | PREPARED, NOT RUN | No GPU repository has been uploaded or published |
| Public release | NOT READY | Complete GPU numerical tests, sanitizer checks and hardware evidence first |

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
Kubernetes configuration and billing settings were not changed. No cluster job or
new resource was provisioned.

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

## Remaining GPU-access gate

The EIDF GPU Service is accessed through a project Kubernetes connection file
(`kubeconfig`); the client VM does not itself need a GPU. The default connection
file is missing from the current user account, and no current context is set.
A historical A100 hardware record is not proof of current allocation or access.
Project Leads/Managers can supply or deploy the connection file through the portal.
See the [official GPU Service FAQ](https://docs.eidf.ac.uk/services/gpuservice/faq/).

Once access is restored: inspect the existing project queue/quota, run bounded
GPU checks in the authorized allocation, save all four Compute Sanitizer outputs,
then collect repeated transfer-inclusive and resident GPU measurements. Do not
change quotas, attach paid services or expose privileged runners to pull requests.
