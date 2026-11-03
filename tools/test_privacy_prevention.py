"""Integration checks for future metadata, native builds and local Git hooks."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


TOOLS = Path(__file__).parent


def benchmark_module():
    spec = importlib.util.spec_from_file_location('privacy_test_benchmark', TOOLS / 'benchmark_all.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PreventionTests(unittest.TestCase):
    def test_portable_runtime_library_path_preserves_solver_settings(self):
        runner = benchmark_module()
        settings = {'seconds': 280}
        variant = {'env': {'LD_LIBRARY_PATH': '${STUDY}/runtime', 'MIP': '1'}}
        with tempfile.TemporaryDirectory() as directory:
            actual = runner.clean_env(settings, variant, 121, Path(directory))
            observation = runner.public_record(actual, runner.ROOT)
        self.assertEqual(actual['LD_LIBRARY_PATH'], directory + '/runtime')
        self.assertEqual(actual['TL'], '280')
        self.assertEqual(actual['NT'], '2')
        self.assertEqual(actual['SEED'], '121')
        self.assertEqual(actual['MIP'], '1')
        self.assertEqual(observation['LD_LIBRARY_PATH'], '<local-environment-omitted>')
        self.assertEqual(variant['env']['LD_LIBRARY_PATH'], '${STUDY}/runtime')

    @unittest.skipUnless(shutil.which('g++'), 'g++ unavailable')
    def test_native_build_does_not_embed_absolute_source_filename(self):
        runner = benchmark_module()
        runner.STOP.clear()
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            tree = out / 'sources' / 'fake' / 'tree'
            tree.mkdir(parents=True)
            code = b'#include <iostream>\nint main(){ std::cout << __FILE__; }\n'
            (tree / 'main.cpp').write_bytes(code)
            source = {'language': 'cpp', 'entry': 'main.cpp', 'aliases': ['fixture/main.cpp'],
                      'files': {'main.cpp': runner.sha(tree / 'main.cpp')},
                      'effective_sha256': hashlib.sha256(code).hexdigest()}
            result = runner.build_source(out, {'sources': {'fake': source}, 'compiler': 'g++'}, 'fake')
            binary = tree.parent / 'solution'
            self.assertTrue(result['ok'])
            self.assertNotIn(str(tree).encode(), binary.read_bytes())
            self.assertEqual(subprocess.check_output([str(binary)]).decode(), './main.cpp')

    def test_hook_uses_relative_private_config_and_wrapper_uses_utc(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo = base / 'repo'
            repo.mkdir()
            env = {key: value for key, value in os.environ.items()
                   if key not in {'GIT_AUTHOR_DATE', 'GIT_COMMITTER_DATE', 'GIT_AUTHOR_NAME',
                                  'GIT_AUTHOR_EMAIL', 'GIT_COMMITTER_NAME', 'GIT_COMMITTER_EMAIL'}}
            env['TZ'] = 'Etc/GMT-5'
            def git(*args):
                return subprocess.run(['git', '-C', str(repo), *args], env=env, capture_output=True, text=True)
            self.assertEqual(git('init', '-q').returncode, 0)
            git('config', 'user.name', 'public-account')
            git('config', 'user.email', 'public@users.noreply.github.com')
            git('config', 'privacy.configFile', '../private.json')
            git('config', 'core.hooksPath', '.githooks')
            (base / 'private.json').write_text(json.dumps({'forbidden_literals': ['Synthetic Identity']}))
            (repo / 'tools').mkdir()
            (repo / '.githooks').mkdir()
            for name in ('privacy_check.py', 'privacy-commit'):
                shutil.copy2(TOOLS / name, repo / 'tools' / name)
            for name in ('pre-commit', 'commit-msg'):
                hook_source = TOOLS.parent / '.githooks' / name
                shutil.copy2(hook_source, repo / '.githooks' / name)
            target = repo / 'evidence.txt'
            target.write_text('Synthetic Identity')
            git('add', '.')
            failed = git('commit', '-qm', 'blocked fixture')
            self.assertNotEqual(failed.returncode, 0)
            self.assertNotIn('Synthetic Identity', failed.stdout + failed.stderr)
            target.write_text('safe record')
            git('add', 'evidence.txt')
            private_message = git('commit', '-qm', 'Synthetic Identity')
            self.assertNotEqual(private_message.returncode, 0)
            self.assertNotIn('Synthetic Identity', private_message.stdout + private_message.stderr)
            committed = subprocess.run([str(repo / 'tools/privacy-commit'), '-qm', 'safe fixture'],
                                       cwd=repo, env=env, capture_output=True, text=True)
            self.assertEqual(committed.returncode, 0, committed.stdout + committed.stderr)
            dates = git('log', '-1', '--format=%aI %cI').stdout.strip().split()
            self.assertTrue(all(value.endswith(('+00:00', 'Z')) for value in dates), dates)


if __name__ == '__main__':
    unittest.main()
