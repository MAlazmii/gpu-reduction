# GPU Reduction: design and implementation plan

Goal: a small independent C++17/CUDA study of summing float32 arrays with float64
accumulation. Explain when host-device transfer costs dominate GPU work. Preserve
all archived coursework. No assessment source, reports or results are reused.

## Approaches
A CUDA heat backend would belong in Heat MPI rather than duplicate that project.
Reworking the archived wave solver has unresolved publication restrictions.
The selected independent reduction study has a small numerical contract and makes
transfer costs directly observable. This is an implementation choice under the
owner's instruction to start the GPU project using the portfolio quality plan.

## Contract
Input length 1..16,777,216; patterns ones, alternating, ramp, cancellation;
repeats 1..100. CUDA thread counts 64, 128, 256 or 512 (default 256).
Both CPU and CUDA sum float32 inputs in float64. Supported deterministic inputs
have exact binary representations and exactly representable intermediate sums
within these bounds. All repetitions must match independent analytical sums
exactly; no fast-math, relaxed tolerance or skip-validation option.

CPU: single-thread sequential optimized loop. CUDA: grid-stride loading, shared
memory block tree, recursively reduce partial sums using disjoint scratch buffers.
This is an educational implementation, not a claim to outperform CUB or a tuned
multithread CPU library. No arbitrary user arrays, FP32 accumulation, multi-GPU,
profiling or speedup claim in this initial version.

CUDA captures two separate repeated measurements: resident device reduction by
CUDA events (all reduction passes; output download excluded), and wall-clock
H2D + reduction + scalar D2H using pageable host memory. Setup, allocation,
input generation and reference validation are excluded. One warm-up per path.
Every sample is validated; failed runs exit nonzero. JSON stdout contains raw
samples, backend, configuration and CUDA device/runtime metadata.

Python build and benchmark tools record source/binary hashes, commands, compiler,
platform, input description and raw outputs. New result directories only. Failures
preserve diagnostics and an explicit incomplete/failed record. CPU success never
stands in for CUDA correctness. Required GPU tests fail if CUDA is unavailable.

## Safety and release boundary
Work only in this separate repository. Use GitHub's no-reply commit email.
No remote repository publication or new GPU resource provisioning. Validation may
use an isolated copy within the owner-authorized existing EIDF allocation.
No billing changes, paid services, self-hosted PR execution or cluster jobs without
confirmed existing-resource authorization. NVIDIA compilation/runtime/sanitizers
are NOT RUN until actually observed. The existing Mac can validate the CPU path.
The MIT licensing choice is reused for this independently authored project.

## Implementation tasks
- [x] T1: Independent CLI/reference tests; observe failure before implementation.
      Cover length/block boundaries, all patterns, invalid values and JSON results.
- [x] T2: CPU implementation, strict build provenance, sanitizers and clean rebuild.
- [x] T3: CUDA implementation, explicit hardware gate and sanitizer entry point.
- [x] T4: Benchmark evidence and failure/no-overwrite regression tests.
- [x] T5: README, numerical/timing specification, CI preparation and fresh review.

## Review focus
Wrong final partial block; grid-stride coverage above 1024 blocks; incorrect
cancellation arithmetic; accidentally timing asynchronous launch only; evidence
mismatched to the executable. GPU-only checks must be distinguished from CPU CI.

## Execution ledger
- Local work follows the already authorized portfolio plan; new reduction scope
  chosen to avoid copying restricted coursework and duplicating Heat MPI.
- Initial executable contract failed because no executable existed; the CPU
  implementation then satisfied numerical and input-validation cases.
- Ruling: accept zero ticks for tiny timing cases. The steady clock returned zero
  for sub-tick work; inventing a positive duration would misrepresent measurements.
  Benchmark summaries retain zero flags; no speedup ratio is inferred.
- Reviewer identified ancestor Git metadata and mismatched build/provenance inputs.
  Both were reproduced with regression tests before correction. Build targets now
  regenerate binary+manifest together, trading a short rebuild for reproducibility.
- EIDF read-only access could not attach to a shared authenticated session. Owner
  explicitly deferred GPU testing; no remote files or compute jobs were created.

CUDA implementation task means source and validation entry points exist; it does
not mark CUDA compilation or execution complete. See validation.md for gates.

- EIDF validation resumed after the owner opened a working shared SSH connection.
  Source archive copied into a fresh isolated directory; checksum verified. Linux
  CPU tests/sanitizers/benchmarks and CUDA 12/13 compilation passed. GPU execution
  remains blocked by no visible device and missing GPU-service configuration.
  No original coursework, driver, billing or cluster resources were changed.

- The missing-config diagnosis was corrected: login shells set KUBECONFIG to the
  existing `/kubernetes/config`. Read-only namespace/queue/quota checks succeeded.
  One bounded job in the existing allocation passed GPU tests, all four sanitizer
  tools and CPU/GPU benchmark reproduction on an A100 40 GB. Credentials and
  coursework remained unchanged. Full evidence was saved locally and on the VM.
