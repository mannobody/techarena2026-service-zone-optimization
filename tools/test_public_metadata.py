import copy
from pathlib import Path
from unittest import mock
import unittest

from public_metadata import public_record


class PublicMetadataTests(unittest.TestCase):
    def test_observation_copy_preserves_execution_and_benchmark_parameters(self):
        home = Path('/' + 'home/' + 'synthetic-person')
        root = home / 'project'
        original = {
            'command': ['/usr/bin/time', str(root / 'candidate'), '280'],
            'env': {'PATH': str(home / 'bin') + ':/usr/bin', 'HOME': str(home),
                    'NT': '2', 'TL': '280', 'SEED': '121', 'MIP': '1'},
            'host': {'node': 'synthetic-device', 'cpu_model': 'Synthetic CPU', 'machine': 'x86_64',
                     'topology': 'synthetic complete host layout',
                     'cpu_topology': 'synthetic complete host core list'},
            'branch': 'synthetic-person/experiment', 'score': 198.25,
        }
        before = copy.deepcopy(original)
        with mock.patch.object(Path, 'home', return_value=home):
            output = public_record(original, root)
        self.assertEqual(original, before)
        self.assertEqual(output['command'], ['/usr/bin/time', './candidate', '280'])
        self.assertEqual(output['env']['NT'], '2')
        self.assertEqual(output['env']['TL'], '280')
        self.assertEqual(output['env']['SEED'], '121')
        self.assertEqual(output['score'], original['score'])
        self.assertNotIn('synthetic-person', repr(output))
        self.assertNotIn('synthetic-device', repr(output))
        self.assertEqual(output['host']['topology'], '<local-host-omitted>')
        self.assertEqual(output['host']['cpu_topology'], '<local-host-omitted>')

    def test_nested_keys_pathobjects_and_friend_data(self):
        home = Path('/' + 'home/' + 'synthetic-person')
        root = home / 'project'
        original = {str(root / 'input.json'): [root / 'out.json'],
                    'friend': {'name': 'other-author', 'email': 'other@example.test'}}
        with mock.patch.object(Path, 'home', return_value=home):
            output = public_record(original, root)
        self.assertIn('./input.json', output)
        self.assertEqual(output['./input.json'], ['./out.json'])
        self.assertEqual(output['friend'], original['friend'])


if __name__ == '__main__':
    unittest.main()
