"""Compile and bind the command, sources and binary into a build manifest."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    output = Path(sys.argv[1]).resolve()
    command = sys.argv[2:]
    manifest = output.with_suffix('.build.json')
    manifest.unlink(missing_ok=True)
    sources = {str(p.relative_to(ROOT)): sha256(p)
               for p in sorted((ROOT / 'src').glob('*')) if p.is_file()}
    compiler = subprocess.run([command[0], '--version'], text=True, capture_output=True,
                              timeout=30, check=True).stdout
    subprocess.run(command, check=True, timeout=300)
    for name, digest in sources.items():
        if sha256(ROOT / name) != digest:
            raise RuntimeError('Source changed during build: ' + name)
    manifest.write_text(json.dumps({'command': command, 'compiler': compiler,
                                   'source_sha256': sources, 'binary_sha256': sha256(output)},
                                  indent=2) + '\n')


if __name__ == '__main__':
    main()
