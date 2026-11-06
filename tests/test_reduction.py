"""Executable contract checks with an independent Python numerical oracle."""
import json
import math
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = os.environ.get('REDUCTION_BACKEND', 'cpu')
BINARY = Path(os.environ.get('REDUCTION_BINARY', str(ROOT / 'build' / ('reduce_' + BACKEND))))


def expected(n, pattern):
    if pattern == 'ones':
        return float(n)
    if pattern == 'alternating':
        return float(n % 2)
    if pattern == 'ramp':
        return math.fsum((i % 1024 - 512) / 512 for i in range(n))
    return math.fsum((100000000.0, 1.0, -100000000.0, 1.0)[i % 4] for i in range(n))


class ReductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if BACKEND not in ('cpu', 'cuda'):
            raise AssertionError('REDUCTION_BACKEND must be cpu or cuda')
        if not BINARY.is_file():
            raise AssertionError('Required executable missing: ' + str(BINARY))

    def run_case(self, args):
        return subprocess.run([str(BINARY), *map(str, args)], text=True,
                              capture_output=True, timeout=60)

    def check_case(self, n, pattern, threads=None):
        args = [n, pattern, 2]
        if threads is not None:
            args.append(threads)
        r = self.run_case(args)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertEqual((d['backend'], d['n'], d['pattern']), (BACKEND, n, pattern))
        self.assertEqual(d['validation'], 'pass')
        self.assertEqual(d['expected'], expected(n, pattern))
        self.assertEqual(len(d['samples']), 2)
        self.assertEqual(d['precision'], 'float32 input / float64 accumulation')
        for sample in d['samples']:
            self.assertEqual(sample['sum'], expected(n, pattern))
            if BACKEND == 'cuda':
                self.assertEqual(sample['transfer_sum'], expected(n, pattern))
                self.assertGreaterEqual(sample['resident_seconds'], 0)
                self.assertGreater(sample['transfer_seconds'], 0)
                self.assertTrue(d['device'])
                self.assertEqual(d['threads'], threads or 256)
            else:
                self.assertGreaterEqual(sample['cpu_seconds'], 0)
                self.assertNotIn('resident_seconds', sample)
                self.assertIsNone(d['threads'])

    def test_reference_and_block_boundaries(self):
        for n in (1, 2, 3, 4, 31, 32, 33, 63, 64, 65, 127, 128, 129,
                  255, 256, 257, 511, 512, 513, 1023, 1024, 1025):
            for pattern in ('ones', 'alternating', 'ramp', 'cancellation'):
                with self.subTest(n=n, pattern=pattern):
                    self.check_case(n, pattern)

    def test_grid_stride_and_multiple_passes(self):
        for n in (65537, 262161, 1048577):
            self.check_case(n, 'ramp')
            self.check_case(n, 'cancellation')

    def test_block_configuration_contract(self):
        if BACKEND == 'cuda':
            for threads in (64, 128, 256, 512):
                self.check_case(1048593, 'cancellation', threads)
                self.check_case(threads + 1, 'ramp', threads)
        else:
            self.assertNotEqual(self.run_case([10, 'ones', 1, 256]).returncode, 0)

    def test_reject_invalid_inputs(self):
        bad = ([], ['0', 'ones', '1'], ['-1', 'ones', '1'],
               ['16777217', 'ones', '1'], ['999999999999999999999', 'ones', '1'],
               ['1.5', 'ones', '1'], ['+1', 'ones', '1'], [' 1', 'ones', '1'],
               ['1', 'unknown', '1'], ['1', 'ones', '0'], ['1', 'ones', '101'],
               ['1', 'ones', '-1'], ['1', 'ones', '1x'], ['1', 'ones', '1', '63'],
               ['1', 'ones', '1', '1024'], ['1', 'ones', '1', '256', 'extra'])
        for args in bad:
            with self.subTest(args=args):
                r = self.run_case(args)
                self.assertNotEqual(r.returncode, 0)
                self.assertTrue(r.stderr.strip())
                self.assertEqual(r.stdout, '')


if __name__ == '__main__':
    unittest.main()
