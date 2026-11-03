#!/usr/bin/env python3
"""Profile selection and dependency checks only; never runs optimization."""
import collections
import importlib.util
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import MagicMock, patch

SPEC = importlib.util.spec_from_file_location('benchmark_compare', Path(__file__).with_name('benchmark_compare.py'))
b = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(b)


def candidates():
    rng = random.Random(20261020)
    result = []
    anchors = list(b.ANCHORS)
    def add(name, group):
        cid = b.runner.digest(name.encode())
        result.append({'id': cid, 'bucket': group, 'aliases': [name],
                       'vector': [rng.random() for _ in range(19)]})
    for i, a in enumerate(anchors):
        group = ('medium' if i in (0, 3) else 'small') if i < 5 else (
                 'tiny' if i < 9 else 'medium' if a.endswith('/anti.json') else 'small')
        add(a, group)
    for group, quota in b.QUOTAS.items():
        for i in range(quota*3):
            add(f'fixture/{group}_{i}.json', group)
    return result


class ProfileTests(unittest.TestCase):
    def test_deterministic_diverse_balanced_selection(self):
        cases = candidates()
        selected, reasons, loads = b.choose_cases(cases, [1, 2, 3], 5)
        self.assertEqual((selected, reasons, loads), b.choose_cases(cases, [1, 2, 3], 5))
        by_id = {c['id']: c for c in cases}
        self.assertEqual(len(set(selected)), 30)
        self.assertEqual(collections.Counter(by_id[c]['bucket'] for c in selected), b.QUOTAS)
        for alias in b.ANCHORS:
            self.assertTrue(any(alias in by_id[c]['aliases'] for c in selected))
        expected = [sum(b.slot_counts(c, [1, 2, 3], 5)[i] for c in selected) for i in range(5)]
        self.assertEqual(loads, expected)
        self.assertEqual(sum(loads), 90)
        self.assertLessEqual(max(loads)-min(loads), 2)

    def test_insufficient_category_is_an_error(self):
        with self.assertRaisesRegex(ValueError, 'недостаточно'):
            b.choose_cases([c for c in candidates() if c['bucket'] != 'huge'], [1, 2, 3])

    def test_missing_anchor_is_an_error(self):
        with self.assertRaisesRegex(ValueError, 'обязательный'):
            b.choose_cases([c for c in candidates() if b.ANCHORS[0] not in c['aliases']], [1, 2, 3])

    def test_features_handle_empty_and_degenerate_inputs(self):
        x = {'sites': [], 'offices': [], 'workers': [], 'distances': [],
             'maxDifference': 0, 'balanceCoefficient': 0}
        self.assertEqual(len(b.features(x)), 19)
        x.update({'sites': [{'x': 0, 'y': 0, 'reward': 0, 'tasks': [1, 2]}],
                  'offices': [{'x': 0, 'y': 0, 'maxSize': 0, 'cost': 0}], 'distances': [[0]]})
        vector = b.features(x)
        self.assertEqual(vector[5], 1)  # All task skills are unavailable.
        self.assertGreater(vector[12], 0)  # Duplicate coordinates.

    def test_incompatible_highs_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / 'fake.so'
            source.write_bytes(b'unit-test, not a shared library')
            api = MagicMock()
            api.Highs_create.return_value = 123
            api.Highs_getSizeofHighsInt.return_value = 8
            with patch.object(b.ctypes, 'CDLL', return_value=api):
                with self.assertRaisesRegex(ValueError, '32-bit'):
                    b.prepare_library(root / 'out', source)
            api.Highs_destroy.assert_called_once_with(123)


if __name__ == '__main__':
    unittest.main()
