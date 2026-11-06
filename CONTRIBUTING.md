# Contributing

Run `make test` and `make sanitize` after CPU/shared-code changes. CUDA changes
also require `make test-cuda` and `make gpu-sanitize` on real NVIDIA hardware.
Report which checks were not run. A successful CPU workflow is not GPU approval.

Keep numerical inputs, accumulation precision, tolerances and timing boundaries
explicit. Add an independent expectation for new numerical cases. Never skip a
failed check, turn missing hardware into success, or rewrite measurements by hand.
Preserve diagnostics, source/binary hashes and raw repeated samples. Do not enable
fast-math silently. Clean-build after changing compiler flags or architecture.

Never commit secrets, cluster configuration, private paths, coursework archives,
compiled binaries or unreviewed local benchmark dumps. New output directories must
not overwrite previous results. GPU jobs run manually in an approved allocation;
do not attach privileged cluster runners to untrusted pull requests.
