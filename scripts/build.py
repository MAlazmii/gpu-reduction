"""Compile and bind the command, sources and binary into a build manifest."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    output = Path(sys.argv[1]).absolute()
    command = sys.argv[2:]
    if len(command) < 3 or command[-2] != '-o' or Path(command[-1]).absolute() != output:
        raise ValueError('Compiler command must end with -o OUTPUT')
    manifest = output.with_suffix('.build.json')
    manifest.unlink(missing_ok=True)
    sources = {str(p.relative_to(ROOT)): sha256(p)
               for p in sorted((ROOT / 'src').glob('*')) if p.is_file()}
    compiler = subprocess.run([command[0], '--version'], text=True, capture_output=True,
                              timeout=30, check=True).stdout
    with tempfile.TemporaryDirectory(prefix='.reduction-build-', dir=output.parent) as directory:
        staged_output = Path(directory) / output.name
        build_command = [*command[:-1], str(staged_output)]
        subprocess.run(build_command, check=True, timeout=300)
        if staged_output.is_symlink() or not staged_output.is_file():
            raise RuntimeError('Compiler did not produce a binary')
        for name, digest in sources.items():
            if sha256(ROOT / name) != digest:
                raise RuntimeError('Source changed during build: ' + name)
        staged_manifest = Path(directory) / manifest.name
        staged_manifest.write_text(json.dumps({
            'command': command, 'compiler': compiler, 'source_sha256': sources,
            'binary_sha256': sha256(staged_output),
        }, indent=2) + '\n')
        staged_output.replace(output)
        staged_manifest.replace(manifest)


if __name__ == '__main__':
    main()
