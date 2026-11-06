# Numerical contract

Compute s = sum(x[i], i=0..N-1). Inputs are float32; every CPU/GPU accumulator and
partial sum is float64. Do not enable fast-math or change precision when comparing
implementations. N is bounded by 2^24 to limit allocations and keep these inputs'
intermediate sums exactly representable.

| Pattern | x[i] | Analytical sum |
|---|---|---|
| ones | 1 | N |
| alternating | +1 for even i, -1 otherwise | N mod 2 |
| ramp | ((i mod 1024) - 512) / 512 | -q + (r(r-1)/2 - 512r)/512; q=N div 1024, r=N mod 1024 |
| cancellation | Repeating [100000000, 1, -100000000, 1] | 2q + [0, 100000000, 100000001, 1][r]; q=N div 4, r=N mod 4 |

The input integers, including 100000000, are exactly representable in float32.
Ramp denominators are powers of two. For cancellation, even summing all positive
terms before negatives remains below 2^53 at the maximum N. For the ramp, sums
scaled by 512 remain below 2^53. Thus every intermediate double sum is exact for
any grouping of these supported inputs. The required absolute error is **zero**.
This contract is intentionally narrower than summing arbitrary real-valued inputs;
it does not promise zero error for general floating-point reductions.

The C++ analytical reference is separate from the generating/reduction loops.
Python tests build an independent expectation with `math.fsum`, exercising partial
blocks, multiple passes and grid-stride coverage. Cancellation catches accidental
float32 accumulation. All measured repetitions and warm-ups are validated. Missing
hardware is NOT RUN, never a numerical pass.

Design references (no source code copied):
- [CUDA best practices](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html): timing, precision, memory transfers.
- [Compute Sanitizer](https://docs.nvidia.com/compute-sanitizer/ComputeSanitizer/index.html): memory, initialization, races and synchronization.
