"""Require real CUDA validation; a missing tool/device is an error, not a skip."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
for tool in ('memcheck', 'racecheck', 'initcheck', 'synccheck'):
    for n in (1, 257, 262161):
        subprocess.run(['compute-sanitizer', '--tool', tool, '--error-exitcode', '99',
                        str(ROOT / 'build/reduce_cuda'), str(n), 'cancellation', '1', '256'],
                       cwd=ROOT, check=True, timeout=180)
