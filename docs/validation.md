# Validation status

Observed 6 November 2026. This project is a local development candidate. The Mac
has no CUDA compiler on PATH; no NVIDIA device or EIDF GPU execution was verified.
The owner deferred EIDF testing. Nothing here treats CPU results as GPU evidence.

| Check | Status | Evidence and limit |
|---|---|---|
| Independent implementation | PASS | No recovered coursework source or results copied; separate project directory |
| Strict CPU build | PASS locally | Apple clang 21, C++17, warnings treated as errors |
| CPU contract and evidence tests | PASS locally | 10 unittest methods; includes many numerical/input configurations |
| CPU AddressSanitizer/UBSan | PASS locally | All four executable-contract test methods under instrumentation |
| CPU benchmark reproduction | PASS locally | Three sizes, five raw repetitions each; exact analytical validation |
| Independent static review | PASS after fixes | No observed numerical/indexing blocker; two provenance findings reproduced and corrected |
| Clean-directory CPU build | PASS locally | No installed project package or archived files are required |
| CUDA compilation | NOT RUN | Requires NVIDIA CUDA toolchain; unavailable locally |
| CUDA numerical tests | NOT RUN | Requires approved real NVIDIA GPU access |
| Compute Sanitizer | NOT RUN | memcheck, racecheck, initcheck, synccheck must all pass |
| GPU performance | NOT RUN | No GPU timings, speedup, bandwidth or optimization claim |
| GitHub CPU workflow | PREPARED, NOT RUN | No GPU repository has been uploaded or published |
| Public release | NOT READY | Complete CUDA build, numerical tests, sanitizer checks and hardware evidence first |

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
