"""Loopback HTTP fixtures exercise bridge validation without real VM credentials."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import http.client
import json
import threading
import unittest

from scripts import lab_tls_bridge as bridge


class FakeUpstream(BaseHTTPRequestHandler):
    calls = []
    response_code = 200
    response_body = b'{"state":"idle","session_id":null,"expires_at":null,"job":null}'
    response_type = 'application/json'

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        type(self).calls.append((self.path, dict(self.headers), body))
        self.send_response(type(self).response_code)
        self.send_header('Content-Type', type(self).response_type)
        self.send_header('Content-Length', str(len(type(self).response_body)))
        self.end_headers()
        self.wfile.write(type(self).response_body)


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstream = ThreadingHTTPServer(('127.0.0.1', 0), FakeUpstream)
        cls.bridge = bridge.AgentBridgeServer(0, cls.upstream.server_port)
        cls.threads = []
        for server in (cls.upstream, cls.bridge):
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            cls.threads.append(thread)

    @classmethod
    def tearDownClass(cls):
        for server in (cls.bridge, cls.upstream):
            server.shutdown()
            server.server_close()
        for thread in cls.threads:
            thread.join(timeout=2)

    def setUp(self):
        FakeUpstream.calls.clear()
        FakeUpstream.response_code = 200
        FakeUpstream.response_body = b'{"state":"idle"}'
        FakeUpstream.response_type = 'application/json'

    def connection(self):
        return http.client.HTTPConnection('127.0.0.1', self.bridge.server_port, timeout=3)

    def request(self, method='POST', path=bridge.AGENT_PATH, body=b'{"result":null}', headers=None):
        connection = self.connection()
        try:
            connection.request(method, path, body, headers or {
                'Authorization': 'Bearer ' + 'x' * 40, 'Content-Type': 'application/json'})
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()

    def test_forwards_only_agent_path_and_approved_headers(self):
        status, body = self.request(headers={'Authorization': 'Bearer ' + 'x' * 40,
            'Content-Type': 'application/json', 'Cookie': 'browser=secret',
            'Origin': 'https://untrusted.invalid', 'X-Forwarded-Host': 'evil.invalid'})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['state'], 'idle')
        path, headers, body = FakeUpstream.calls[0]
        self.assertEqual(path, bridge.AGENT_PATH)
        self.assertEqual(body, b'{"result":null}')
        self.assertEqual(headers['Host'], f'127.0.0.1:{self.upstream.server_port}')
        for name in ('Cookie', 'Origin', 'X-Forwarded-Host'):
            self.assertNotIn(name, headers)

    def test_multiple_polls_share_one_http_connection(self):
        connection = self.connection()
        try:
            for _ in range(3):
                connection.request('POST', bridge.AGENT_PATH, b'{}', {
                    'Authorization': 'Bearer ' + 'x' * 40, 'Content-Type': 'application/json'})
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                response.read()
            self.assertEqual(len(FakeUpstream.calls), 3)
        finally:
            connection.close()

    def test_routes_and_methods_are_restricted(self):
        for path in ('/', '/login', '/api/lab-agent/poll?x=1', '/api/lab-agent/poll/'):
            self.assertEqual(self.request(path=path)[0], 404)
        self.assertEqual(self.request(method='GET')[0], 405)
        self.assertEqual(FakeUpstream.calls, [])

    def test_missing_credentials_content_type_and_bad_json_rejected(self):
        self.assertEqual(self.request(headers={'Content-Type': 'application/json'})[0], 401)
        self.assertEqual(self.request(headers={'Content-Type': 'text/plain'})[0], 415)
        self.assertEqual(self.request(body=b'[]')[0], 400)
        self.assertEqual(self.request(body=b'bad')[0], 400)
        self.assertEqual(FakeUpstream.calls, [])

    def test_oversized_and_chunked_payloads_rejected(self):
        self.assertEqual(self.request(body=b'x' * 65537)[0], 413)
        self.assertEqual(self.request(headers={'Content-Type': 'application/json',
            'Transfer-Encoding': 'chunked'})[0], 400)
        self.assertEqual(FakeUpstream.calls, [])

    def test_unapproved_upstream_replies_do_not_leak(self):
        for code, body, content_type in ((302, b'{"internal":"private"}', 'application/json'),
                (500, b'secret traceback', 'text/html'),
                (200, b'{"x":"' + b'a'*65537 + b'"}', 'application/json'),
                (200, b'[]', 'application/json')):
            FakeUpstream.response_code = code
            FakeUpstream.response_body = body
            FakeUpstream.response_type = content_type
            status, payload = self.request()
            self.assertEqual(status, 502)
            self.assertNotIn(b'private', payload)
            self.assertNotIn(b'traceback', payload)

    def test_allowed_json_errors_are_preserved(self):
        FakeUpstream.response_code = 409
        FakeUpstream.response_body = b'{"error":"conflict"}'
        self.assertEqual(self.request(), (409, b'{"error":"conflict"}'))


if __name__ == '__main__':
    unittest.main()
