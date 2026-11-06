"""Verify rebuilding repairs provenance after edits and missing manifests."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BuildTests(unittest.TestCase):
    def test_rebuild_tracks_all_sources_and_repairs_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / 'src', root / 'src')
            (root / 'scripts').mkdir()
            shutil.copy2(ROOT / 'scripts/build.py', root / 'scripts/build.py')
            shutil.copy2(ROOT / 'Makefile', root / 'Makefile')
            command = ['make', 'CXX=' + os.environ.get('TEST_CXX', 'c++'), 'cpu']
            def build():
                r = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=60)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            build()
            source = root / 'src/cuda.cu'
            source.write_text(source.read_text() + '\n// provenance regression edit\n')
            build()
            manifest = root / 'build/reduce_cpu.build.json'
            self.assertEqual(json.loads(manifest.read_text())['source_sha256']['src/cuda.cu'],
                             hashlib.sha256(source.read_bytes()).hexdigest())
            manifest.unlink()
            build()
            self.assertTrue(manifest.is_file())


if __name__ == '__main__':
    unittest.main()
