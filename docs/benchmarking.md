# Measurement protocol

1. Record compiler, driver, GPU model and compute capability. Use an allocated
   GPU under existing EIDF authorization; do not run experiments on a login host.
2. Clean-build CPU and CUDA with matching precision and no fast-math. Run the full
   contract tests, then `make gpu-sanitize`. Profiling and sanitizer instrumentation
   must not be active during performance measurements.
3. Use a new output folder. Run `scripts/benchmark.py NEW --backend both --repeats 5`.
   Default sizes are 4096, 65537 and 1048577, with the cancellation pattern. Expand
   sizes only within the documented cap. CPU and GPU use identical input values.
4. Keep every raw sample. Compare median and min/max variation. Investigate zero
   timing readings (below clock resolution) or noisy results; do not divide by a
   zero duration or present such ratios as measured speedups.
5. Record device contention, power/clock settings and relevant system conditions
   alongside the results. These are not automatically controlled by the program.

CPU time uses `steady_clock`. CUDA resident timing uses events on the default
stream around every reduction pass; this is an elapsed device interval, including
possible gaps between host-issued launches. Event synchronization catches execution
errors. A scalar download follows and is outside the resident interval.

The transfer-inclusive path uses a host steady clock around blocking upload,
reduction and blocking scalar download. The `std::vector` host buffer is pageable,
so runtime staging costs are included. Context initialization, memory allocation,
input generation and validation are excluded. Consequently this is a reusable-buffer
latency study, not total first-invocation application latency. Each path is warmed
up once. Resident measurement precedes transfer-inclusive measurement within each
repetition; this ordering is fixed and must be reported when interpreting results.

CPU is one optimized sequential thread. It is not a tuned multithread library
baseline. CUDA uses float64 accumulation, whose throughput varies across devices.
This first version contains no comparative performance claims or invented plots.
Future profiling should compare with a library such as CUB at matched precision
before describing the custom kernel as competitive.

The archive checks build fingerprints before and after measurements and records
source/script/test hashes. Raw output and errors are retained, including timeouts.
Completed configurations are saved incrementally; if a process is interrupted,
its internal partial repetitions may not be available because stdout is emitted
only on completion. `complete` is set only after every requested backend/size
finishes successfully. A source fingerprint is stronger than a commit label if
the working tree was modified; both are recorded explicitly.
