#!/usr/bin/env python3
"""Short integration tests; never starts real optimization solvers."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile

SCRIPT = Path(__file__).with_name('benchmark_all.py').resolve()
PROJECT = SCRIPT.parents[1]
spec = importlib.util.spec_from_file_location('benchmark_all', SCRIPT)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

CPP = r'''
#include <fstream>
#include <cstdlib>
#include <chrono>
#include <thread>
#include <iostream>
int main(int argc, char** argv) {
 std::string inp = argc > 1 ? argv[1] : "instance.json";
 std::string out = argc > 2 ? argv[2] : "solution.json";
 double limit = argc > 3 ? atof(argv[3]) : 280.0;
 {std::ofstream f(out); f << "[{\"officeId\":0,\"sites\":[0],\"workers\":[]}]";}
 std::cerr << "threads=" << getenv("NT") << " seed=" << getenv("SEED") << std::endl;
 if (getenv("TEST_HANG")) while(true) std::this_thread::sleep_for(std::chrono::milliseconds(10));
 if (getenv("TEST_DELAY")) std::this_thread::sleep_for(std::chrono::milliseconds(150));
 if (getenv("TEST_INVALID")) {std::ofstream f(out);f << "[broken";}
 return getenv("TEST_FAIL") ? 7 : 0;
}
'''


def instance(reward=10):
    return {'sites': [{'x': 1, 'y': 0, 'reward': reward, 'tasks': []}],
            'offices': [{'x': 0, 'y': 0, 'cost': 1, 'maxSize': 1}],
            'workers': [], 'distances': [[2]], 'maxDifference': 0, 'balanceCoefficient': 0}


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='szo-runner-test-')
        self.base = Path(self.tmp.name)
        self.root, self.out = self.base / 'repo', self.base / 'study'
        for directory in ('task', 'candidate', 'copy'):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        (self.root / 'task/validate_solution.py').write_bytes((PROJECT / 'task/validate_solution.py').read_bytes())
        (self.root / 'candidate/main.cpp').write_text(CPP)
        (self.root / 'copy/main.cpp').write_text(CPP)
        (self.root / 'helper.cpp').write_text('int main(int argc,char**argv){return 0;}')
        (self.root / 'task/a.json').write_text(json.dumps(instance()))
        (self.root / 'task/a_copy.json').write_text(json.dumps(instance(), indent=2))
        (self.root / 'task/b.json').write_text(json.dumps(instance(20)))
        with zipfile.ZipFile(self.root / 'candidate.zip', 'w') as z:
            z.writestr('main.cpp', CPP)
        variants = {name: {'source': 'candidate/main.cpp', 'env': {flag: '1'}}
                    for name, flag in [('hang', 'TEST_HANG'), ('invalid', 'TEST_INVALID'),
                                       ('fail', 'TEST_FAIL'), ('delay', 'TEST_DELAY')]}
        (self.root / 'spec.json').write_text(json.dumps({'variants': variants, 'cases': {}, 'seconds': 1}))
        b.STOP.clear()

    def tearDown(self):
        self.tmp.cleanup()

    def command(self, *args):
        return [sys.executable, str(SCRIPT), *args, '--root', str(self.root), '--out', str(self.out)]

    def cli(self, *args, expect=0):
        r = subprocess.run(self.command(*args), capture_output=True, text=True, timeout=35)
        self.assertEqual(r.returncode, expect, r.stdout + r.stderr)
        return r

    def plan(self, seconds='.2', seeds='11,12'):
        self.cli('plan', '--seconds', seconds, '--seeds', seeds)
        return json.loads((self.out / 'manifest.json').read_text())

    def rows(self):
        return [json.loads(p.read_text()) for p in (self.out / 'runs').glob('*/result.json')]

    def test_discovery_dedup_freeze_resume_and_corruption(self):
        m = self.plan()
        self.assertEqual(len(m['sources']), 1)
        self.assertEqual(len(m['cases']), 2)
        self.assertEqual(len(m['variants']), 5)
        src = next(iter(m['sources'].values()))
        self.assertEqual(len(src['aliases']), 3)  # Two files and one ZIP.
        self.assertFalse(b.full_solver(SCRIPT.read_bytes(), 'python'))
        # Changing a working source/input after plan must not change the study.
        (self.root / 'candidate/main.cpp').write_text('broken source')
        (self.root / 'task/a.json').write_text('{}')
        self.cli('run', '--solver', 'candidate/main.cpp', '--max-runs', '1')
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['status'], 'ok')
        self.assertIn(rows[0]['objective'], (7.0, 17.0))
        self.assertEqual(rows[0]['rss_kb'] > 0, True)
        self.assertTrue(b.cache_valid(self.out, rows[0]))
        altered = dict(rows[0], objective=-123)
        self.assertFalse(b.cache_valid(self.out, altered))
        old_attempt = rows[0]['attempt']
        self.cli('run', '--solver', 'candidate/main.cpp', '--max-runs', '0')
        self.assertEqual(self.rows()[0]['attempt'], old_attempt)
        self.cli('run', '--solver', 'candidate/main.cpp')
        self.assertEqual(len(self.rows()), 4)
        row = self.rows()[0]
        (self.out / row['attempt'] / 'work/solution.json').write_text('[]')
        self.cli('run', '--solver', 'candidate/main.cpp')
        repaired = next(r for r in self.rows() if r['job_id'] == row['job_id'])
        self.assertNotEqual(repaired['attempt'], row['attempt'])
        self.assertTrue(b.cache_valid(self.out, repaired))
        self.cli('run', '--seconds', '280', expect=2)
        self.cli('status')
        self.assertEqual(len(json.loads((self.out / 'results.json').read_text())), 4)

    def test_runtime_invalid_and_timeout_are_cached_but_retryable(self):
        self.plan(seconds='.05', seeds='11')
        for name, status in [('fail', 'runtime_error'), ('invalid', 'invalid'), ('hang', 'timeout')]:
            self.cli('run', '--solver', 'spec.json#' + name, '--case', 'task/a.json')
            rows = [r for r in self.rows() if r['status'] == status]
            self.assertEqual(len(rows), 1)
            before = rows[0]['attempt']
            self.cli('run', '--solver', 'spec.json#' + name, '--case', 'task/a.json')
            self.assertEqual(next(r['attempt'] for r in self.rows() if r['status'] == status), before)
        self.cli('run', '--solver', 'spec.json#invalid', '--case', 'task/a.json', '--retry-failed')
        self.assertTrue(next(r['attempt'] for r in self.rows() if r['status'] == 'invalid').endswith('attempt-0002'))
        timeout = next(r for r in self.rows() if r['status'] == 'timeout')
        self.assertTrue(timeout['valid'])  # Retain valid incumbent but do not hide TIMEOUT.
        self.assertEqual(timeout['objective'], 7.0)

    def test_sigint_lock_and_resume(self):
        self.plan(seconds='.1', seeds='11')
        args = ['run', '--solver', 'spec.json#hang', '--case', 'task/a.json']
        proc = subprocess.Popen(self.command(*args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if list((self.out / 'runs').glob('*/attempt-*/started.json')):
                    break
                self.assertIsNone(proc.poll())
                time.sleep(.03)
            else:
                self.fail('runner did not start')
            self.cli(*args, expect=2)  # Exclusive study lock.
            self.cli('status')        # Read-only status works while the study is running.
            proc.send_signal(signal.SIGINT)
            stdout, stderr = proc.communicate(timeout=5)
            self.assertEqual(proc.returncode, 130, stdout + stderr)
            self.assertEqual(self.rows(), [])
            self.assertEqual(len(list((self.out / 'runs').glob('*/attempt-*/interrupted.json'))), 1)
            self.cli(*args)
            row = self.rows()[0]
            self.assertEqual(row['status'], 'timeout')
            self.assertTrue(row['attempt'].endswith('attempt-0002'))
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()

    def test_snapshots_and_real_geometry_rule(self):
        m = self.plan(seconds='.25', seeds='11')
        variant = next(v for v in m['variants'].values() if 'spec.json#delay' in v['aliases'])
        case = next(c for c in m['cases'].values() if c['stats']['rewards']['max'] == 10)
        m['snapshots'] = [.04, .08]
        build = b.build_source(self.out, m, variant['source'])
        row = b.execute(self.out, m, variant, case, 11, m['cpu_pairs'][0], build)
        self.assertEqual(row['status'], 'ok')
        self.assertEqual(len(row['snapshots']), 2)
        self.assertTrue(all(s['valid'] and s['objective'] == 7 for s in row['snapshots']))
        # Rectangles cross, but no input point is in both hulls: VALID.
        coords = [(-3, -1), (3, -1), (3, 1), (-3, 1),
                  (-1, -3), (1, -3), (1, 3), (-1, 3)]
        x = {'sites': [{'x': a, 'y': c, 'reward': 1, 'tasks': []} for a, c in coords],
             'offices': [{'x': -3, 'y': -1, 'cost': 0, 'maxSize': 4},
                         {'x': -1, 'y': -3, 'cost': 0, 'maxSize': 4}],
             'workers': [], 'distances': [[0]*8, [0]*8], 'maxDifference': 0, 'balanceCoefficient': 0}
        inp, sol = self.base / 'cross.json', self.base / 'cross.solution.json'
        inp.write_text(json.dumps(x))
        sol.write_text(json.dumps([{'officeId': i, 'sites': list(range(i*4, i*4+4)), 'workers': []}
                                   for i in range(2)]))
        analysis = b.analyse(self.out, inp, sol)
        self.assertTrue(analysis['valid'])
        self.assertEqual(analysis['objective'], 8)
        self.assertEqual(analysis['hull_intersections_without_shared_input_points'][0]['area'], 4)
        # An unused input point in the overlap must now make the same answer INVALID.
        x['sites'].append({'x': 0, 'y': 0, 'reward': 0, 'tasks': []})
        for d in x['distances']:
            d.append(0)
        inp.write_text(json.dumps(x))
        self.assertEqual(b.analyse(self.out, inp, sol)['validation_error'], 'Hull conflict')
        inp.write_text(json.dumps({'sites': [], 'offices': [], 'workers': [], 'distances': [],
                                   'maxDifference': 0, 'balanceCoefficient': 0}))
        sol.write_text('[]')
        empty = b.analyse(self.out, inp, sol)
        self.assertTrue(empty['valid'])
        self.assertNotIn('geometry_analysis_error', empty)

    def test_sigkill_keeps_lock_until_independent_timeout(self):
        self.plan(seconds='.05', seeds='11')
        args = ['run', '--solver', 'spec.json#hang', '--case', 'task/a.json']
        proc = subprocess.Popen(self.command(*args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if list((self.out / 'runs').glob('*/attempt-*/started.json')):
                    break
                self.assertIsNone(proc.poll())
                time.sleep(.02)
            else:
                self.fail('runner did not start')
            time.sleep(.15)  # Let the GNU time/timeout/solver child chain start.
            proc.kill()
            proc.communicate(timeout=5)
            self.cli(*args, expect=2)  # Orphaned job retains the same study lock.
            self.assertEqual(self.rows(), [])
            time.sleep(3.5)  # Independent timeout must reap the orphan even without Python.
            self.cli(*args)
            row = self.rows()[0]
            self.assertEqual(row['status'], 'timeout')
            self.assertTrue(row['attempt'].endswith('attempt-0002'))
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()


if __name__ == '__main__':
    unittest.main()
