# GitHub validation and release

Repository: [MAlazmii/gpu-reduction](https://github.com/MAlazmii/gpu-reduction).
The project was validated privately before its public release review.
The release includes only this independent implementation and curated evidence.

The Ubuntu 24.04 workflow builds with GCC and Clang independently. Each job runs
all CPU/evidence tests, the CPU address/undefined-behavior sanitizer contract suite
and three-repeat CPU benchmark reproduction. Jobs have ten-minute limits, use
standard hosted Linux runners, pinned Actions and read-only repository permissions.
Evidence artifacts are retained for fourteen days. No GPU/privileged self-hosted
runner is attached, and no billing or paid-runner setting is enabled by this workflow.

See the [workflow results](https://github.com/MAlazmii/gpu-reduction/actions/workflows/cpu-validation.yml)
for the exact commit result. A CPU CI pass is not a new CUDA validation. The separate
A100 hardware evidence remains tied to its recorded source fingerprints in
[a100-validation.json](../results/a100-validation.json).

Only this independent project is uploaded. Coursework, local raw logs, EIDF
configuration and credentials are excluded. Author and committer metadata use the
owner's GitHub no-reply email throughout history. A bounded history scan found no
private email, private home path or common credential pattern before upload.

Publication requires reviewing the exact contents and current checks. The recorded
benchmarks are not peak-throughput or universal speedup claims. The host CPU model
and clock/contention controls were not captured in the initial A100 run.
