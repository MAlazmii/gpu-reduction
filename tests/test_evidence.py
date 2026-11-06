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
