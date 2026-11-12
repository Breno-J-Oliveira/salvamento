"""Optional real Docker verification; uses only disposable synthetic instances."""
import os
import secrets
import unittest
import urllib.request
import orchestrator as orch


@unittest.skipUnless(os.environ.get('RUN_DOCKER_TESTS') == '1', 'Docker real opcional')
class IncidentDockerTests(unittest.TestCase):
    def test_two_consoles_are_isolated_and_seed_is_not_exposed(self):
        names = [f'lab-u999991-c999991-{secrets.token_hex(4)}' for _ in range(2)]
        flags = ['CTF{110123456789abcd}', 'CTF{ab0123456789cdef}']
        ports = []
        try:
            for name, flag in zip(names, flags):
                ports.append(orch.start(name, 'cti-lab/incident-01', 5000, flag))
            self.assertNotEqual(ports[0], ports[1])
            for port, expected in zip(ports, ['192.0.2.18', '192.0.2.172']):
                for route in ['/health', '/', '/access', '/events', '/processes', '/changes', '/network']:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}{route}', timeout=5) as response:
                        body = response.read().decode()
                        self.assertEqual(response.status, 200)
                        for flag in flags:
                            self.assertNotIn(flag, body)
                        if route == '/access':
                            self.assertIn(expected, body)
            orch.stop(names[0])
            self.assertFalse(orch.status(names[0]))
            self.assertTrue(orch.status(names[1]))
        finally:
            for name in names:
                orch.stop(name)


if __name__ == '__main__':
    unittest.main()
