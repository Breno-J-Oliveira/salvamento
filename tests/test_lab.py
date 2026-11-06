import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

class LabTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / 'challenges/web-01/app.py'
        spec = importlib.util.spec_from_file_location('challenge_web', path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, {'FLAG': 'CTF{synthetic_test_only}'}):
            spec.loader.exec_module(module)
        self.client = module.app.test_client()

    def test_discovery_path(self):
        self.assertNotIn(b'CTF{', self.client.get('/').data)
        self.assertIn(b'/backup-interno', self.client.get('/robots.txt').data)
        result = self.client.get('/backup-interno')
        self.assertEqual(result.data, b'FLAG: CTF{synthetic_test_only}')
        self.assertEqual(result.mimetype, 'text/plain')

    def test_health_and_unknown_path(self):
        self.assertEqual(self.client.get('/health').json, {'status': 'ok'})
        self.assertEqual(self.client.get('/unknown').status_code, 404)

if __name__ == '__main__':
    unittest.main()
