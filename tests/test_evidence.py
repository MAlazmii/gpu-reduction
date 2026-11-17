"""Regression tests for evidence integrity and diagnostic preservation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('benchmark', ROOT / 'scripts/benchmark.py')
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


class EvidenceTests(unittest.TestCase):
    def test_rejects_false_or_invalid_benchmark_evidence(self):
        record = {
            'backend': 'cpu', 'n': 4, 'pattern': 'cancellation',
            'validation': 'pass', 'precision': 'float32 input / float64 accumulation',
            'expected': 2, 'samples': [{'sum': 2, 'cpu_seconds': 0}],
        }
        self.assertEqual(benchmark.summarize_measurement(record, 'cpu', 4, 1),
                         {'cpu_seconds': {'min': 0, 'median': 0, 'max': 0,
                                          'includes_zero_resolution_sample': True}})
        for field, value in (
            ('sum', 1), ('sum', True), ('cpu_seconds', False),
            ('cpu_seconds', -1), ('cpu_seconds', float('nan')),
            ('cpu_seconds', float('inf')),
        ):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                benchmark.summarize_measurement(
                    {**record, 'samples': [{**record['samples'][0], field: value}]},
                    'cpu', 4, 1)

        for field, value in (
            ('pattern', 'ones'), ('precision', 'float32'), ('expected', 1),
            ('backend', 'cuda'), ('n', True),
        ):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                benchmark.summarize_measurement({**record, field: value}, 'cpu', 4, 1)

        gpu_sample = {'sum': 2, 'transfer_sum': 2, 'resident_seconds': 0.001,
                      'transfer_seconds': 0.002}
        gpu_record = {**record, 'backend': 'cuda', 'samples': [gpu_sample]}
        gpu_summary = benchmark.summarize_measurement(gpu_record, 'cuda', 4, 1)
        self.assertEqual(gpu_summary['transfer_seconds']['median'], 0.002)
        for field, value in (('transfer_sum', 1), ('transfer_seconds', float('nan')),
                             ('resident_seconds', -1)):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                benchmark.summarize_measurement(
                    {**gpu_record, 'samples': [{**gpu_sample, field: value}]}, 'cuda', 4, 1)

    def test_failed_command_preserves_output(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / 'failure'
            with self.assertRaises(subprocess.CalledProcessError):
                benchmark.execute([sys.executable, '-c',
                                   'import sys; print("out"); print("diagnostic",file=sys.stderr); sys.exit(3)'], prefix)
            self.assertIn('out', prefix.with_suffix('.stdout.txt').read_text())
            self.assertIn('diagnostic', prefix.with_suffix('.stderr.txt').read_text())

    def test_timeout_preserves_output(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / 'timeout'
            with self.assertRaises(subprocess.TimeoutExpired):
                benchmark.execute([sys.executable, '-c',
                                   'import time; print("started",flush=True); time.sleep(10)'], prefix, timeout=0.2)
            self.assertIn('started', prefix.with_suffix('.stdout.txt').read_text())

    def test_rejects_changed_binary_or_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'src').mkdir()
            source = root / 'src/example.cpp'
            source.write_text('original')
            binary = root / 'program'
            binary.write_bytes(b'executable')
            manifest = {'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
                        'source_sha256': {'src/example.cpp': hashlib.sha256(source.read_bytes()).hexdigest()}}
            binary.with_suffix('.build.json').write_text(json.dumps(manifest))
            benchmark.validate_build(binary, root)
            binary.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'binary'):
                benchmark.validate_build(binary, root)
            binary.write_bytes(b'executable')
            source.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'source'):
                benchmark.validate_build(binary, root)

    def test_rejects_enclosing_repository_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            subprocess.run(['git', 'init', '-q', str(parent)], check=True)
            child = parent / 'unrelated-project'
            child.mkdir()
            self.assertEqual(benchmark.git_metadata(child),
                             {'commit': None, 'working_tree_clean': None})

    def test_existing_output_is_not_modified(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            marker = path / 'keep.txt'
            marker.write_text('keep')
            r = subprocess.run([sys.executable, str(ROOT / 'scripts/benchmark.py'), str(path)],
                               capture_output=True, text=True, timeout=10)
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual(marker.read_text(), 'keep')
            self.assertEqual(list(path.iterdir()), [marker])


if __name__ == '__main__':
    unittest.main()
