"""Testes isolados do painel fictício do laboratório de investigação."""
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch


class IncidentLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'challenges' / 'incident-01' / 'app.py'
        spec = importlib.util.spec_from_file_location('incident_lab', path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, {'FLAG': 'CTF{ab0123456789cdef}'}):
            spec.loader.exec_module(module)
        cls.client = module.app.test_client()

    def test_health_and_read_only_observation_pages(self):
        self.assertEqual(self.client.get('/health').get_json(), {'status': 'ok'})
        for path in ('/', '/access', '/events', '/processes', '/changes', '/network'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn('fictício'.encode(), response.data)
                self.assertEqual(response.headers['Cache-Control'], 'no-store')
                self.assertEqual(self.client.post(path).status_code, 405)
        self.assertEqual(self.client.get('/unknown').status_code, 404)

    def test_evidence_correlates_without_revealing_flag(self):
        access = self.client.get('/access').get_data(as_text=True)
        events = self.client.get('/events').get_data(as_text=True)
        self.assertIn('192.0.2.172', access)
        self.assertIn('req-b14', access)
        self.assertIn('req-b14', events)
        for path in ('/', '/access', '/events', '/processes', '/changes', '/network', '/health'):
            body = self.client.get(path).get_data(as_text=True)
            self.assertNotIn('CTF{', body)
            self.assertNotIn('ab0123456789cdef', body)
            self.assertNotIn(os.environ.get('FLAG', 'test-secret-flag-never-present'), body)

    def test_operational_noise_has_correlated_context(self):
        changes=self.client.get('/changes').get_data(as_text=True)
        network=self.client.get('/network').get_data(as_text=True)
        events=self.client.get('/events').get_data(as_text=True)
        for body in (changes,network,events):
            self.assertIn('b-19',body)
        self.assertIn('req-b14',network)
        self.assertIn('192.0.2.172',network)
        self.assertIn('198.51.100.44',self.client.get('/access').get_data(as_text=True))

    def test_instance_seed_changes_correlated_address(self):
        path = Path(__file__).resolve().parents[1] / 'challenges' / 'incident-01' / 'app.py'
        spec = importlib.util.spec_from_file_location('other_incident_lab', path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, {'FLAG': 'CTF{cd0123456789abcd}'}):
            spec.loader.exec_module(module)
        response = module.app.test_client().get('/access').get_data(as_text=True)
        self.assertIn('192.0.2.206', response)
        self.assertNotIn('192.0.2.172', response)
        self.assertNotIn('cd0123456789abcd', response)


if __name__ == '__main__':
    unittest.main()
