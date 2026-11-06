"""Validated, non-overwriting benchmark archive. No remote resource provisioning."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execute(command, prefix, timeout=300, env=None):
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                timeout=timeout, env=env)
    except subprocess.TimeoutExpired as error:
        for suffix, data in (('.stdout.txt', error.stdout), ('.stderr.txt', error.stderr)):
            if isinstance(data, bytes):
                data = data.decode(errors='replace')
            prefix.with_suffix(suffix).write_text(data or '')
        raise
    prefix.with_suffix('.stdout.txt').write_text(result.stdout)
    prefix.with_suffix('.stderr.txt').write_text(result.stderr)
    result.check_returncode()
    return result.stdout


def validate_build(binary, root=ROOT):
    manifest = json.loads(binary.with_suffix('.build.json').read_text())
    if sha256(binary) != manifest['binary_sha256']:
        raise ValueError('Changed binary; rebuild before measuring')
    current = {str(p.relative_to(root)): sha256(p) for p in sorted((root / 'src').glob('*')) if p.is_file()}
    if current != manifest['source_sha256']:
        raise ValueError('Changed source; clean rebuild before measuring')
    return manifest


def git_metadata(root=ROOT):
    top = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=root,
                         capture_output=True, text=True)
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root.resolve():
        return {'commit': None, 'working_tree_clean': None}
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True)
    dirty = subprocess.run(['git', 'status', '--porcelain'], cwd=root, capture_output=True, text=True)
    return {'commit': head.stdout.strip() if head.returncode == 0 else None,
            'working_tree_clean': dirty.returncode == 0 and not dirty.stdout.strip()}


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--backend', choices=('cpu', 'cuda', 'both'), default='cpu')
    parser.add_argument('--sizes', type=int, nargs='+', default=[4096, 65537, 1048577])
    parser.add_argument('--repeats', type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 100 or not all(1 <= n <= 16777216 for n in args.sizes):
        parser.error('repeats must be 1..100 and sizes 1..16777216')
    if len(args.sizes) != len(set(args.sizes)):
        parser.error('sizes must be unique')
    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output.resolve()
    report = {'status': 'incomplete', 'created_utc': datetime.now(timezone.utc).isoformat(),
              'platform': platform.platform(), 'machine': platform.machine(), 'python': sys.version,
              'pattern': 'cancellation', 'sizes': args.sizes, 'repeats': args.repeats,
              'scope': 'single process/device; CPU timings are not GPU evidence',
              'source_sha256': {str(p.relative_to(ROOT)): sha256(p)
                               for directory in ('src', 'scripts', 'tests')
                               for p in sorted((ROOT / directory).glob('*')) if p.is_file()},
              'builds': {}, 'runs': []}
    path = output / 'benchmark.json'
    save(path, report)
    try:
        report.update(git_metadata())
        backends = ('cpu', 'cuda') if args.backend == 'both' else (args.backend,)
        for backend in backends:
            binary = ROOT / 'build' / ('reduce_' + backend)
            manifest = validate_build(binary)
            report['builds'][backend] = manifest
            env = dict(os.environ, REDUCTION_BACKEND=backend, REDUCTION_BINARY=str(binary))
            command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_reduction.py', '-v']
            execute(command, output / ('validation-' + backend), timeout=600, env=env)
            save(path, report)
            for n in args.sizes:
                command = [str(binary), str(n), 'cancellation', str(args.repeats)]
                data = json.loads(execute(command, output / (backend + '-' + str(n))))
                if (data['validation'] != 'pass' or data['backend'] != backend or data['n'] != n
                        or len(data['samples']) != args.repeats):
                    raise ValueError('Executable returned incomplete or mismatched evidence')
                if validate_build(binary) != manifest:
                    raise ValueError('Build changed while measuring')
                fields = ('cpu_seconds',) if backend == 'cpu' else ('resident_seconds', 'transfer_seconds')
                summary = {}
                for field in fields:
                    values = [sample[field] for sample in data['samples']]
                    summary[field] = {'min': min(values), 'median': statistics.median(values), 'max': max(values),
                                      'includes_zero_resolution_sample': any(v == 0 for v in values)}
                report['runs'].append({'command': command, 'raw': data, 'summary': summary})
                save(path, report)
        report['status'] = 'complete'
        save(path, report)
    except BaseException as error:
        report['status'] = 'failed'
        report['error'] = str(error)
        save(path, report)
        raise
    print(path)


if __name__ == '__main__':
    main()
