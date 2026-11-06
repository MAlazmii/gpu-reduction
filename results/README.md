# Validation and measurement evidence

`validation-summary.json` tracks observed checks and outstanding GPU gates.
Local machine-specific artifacts live in ignored `local-*` or `eidf-*` directories.
The CPU workflow preserves artifacts for 14 days once run. Retain long-term copies
privately and curate publishable results after reviewing host metadata.

CPU timings cannot establish GPU performance. Do not publish benchmark charts until
real GPU execution, required numerical tests and Compute Sanitizer checks pass.
