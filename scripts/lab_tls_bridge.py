"""Loopback-only HTTPS bridge exposing the remote-agent poll endpoint."""
import argparse
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import ssl

AGENT_PATH = '/api/lab-agent/poll'
BODY_LIMIT = 65536
ALLOWED_STATUSES = {200, 400, 401, 409, 413, 429, 503}


class AgentBridgeHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server_version = 'PurpleAgentBridge'
    sys_version = ''

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, format, *args):
        # Request headers, tokens, commands and results never enter bridge logs.
        pass

    def reply(self, status, payload, close=False):
        if close:
            self.close_connection = True
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if self.close_connection:
            self.send_header('Connection', 'close')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(payload)

    def error_json(self, status, close=True):
        self.reply(status, json.dumps({'error': 'Request could not be completed.'}).encode(), close)

    def send_error(self, code, message=None, explain=None):
        self.error_json(code)

    def do_POST(self):
        if self.path != AGENT_PATH:
            self.error_json(404)
            return
        lengths = self.headers.get_all('Content-Length', [])
        if (self.headers.get('Transfer-Encoding') is not None or len(lengths) != 1
                or not re.fullmatch(r'[0-9]{1,8}', lengths[0])):
            self.error_json(400)
            return
        length = int(lengths[0])
        if length > BODY_LIMIT:
            self.error_json(413)
            return
        if length < 1:
            self.error_json(400)
            return
        if (self.headers.get_content_type() != 'application/json'
                or self.headers.get('Content-Encoding') is not None):
            self.error_json(415)
            return
        credentials = self.headers.get_all('Authorization', [])
        if len(credentials) != 1 or not re.fullmatch(r'Bearer [A-Za-z0-9_-]{32,256}', credentials[0]):
            self.error_json(401)
            return
        try:
            body = self.rfile.read(length)
            if len(body) != length:
                self.error_json(400)
                return
            if not isinstance(json.loads(body), dict):
                self.error_json(400)
                return
        except (ValueError, OSError):
            self.error_json(400)
            return
        upstream = http.client.HTTPConnection('127.0.0.1', self.server.app_port, timeout=10)
        try:
            upstream.request('POST', AGENT_PATH, body=body, headers={
                'Authorization': credentials[0], 'Content-Type': 'application/json'})
            response = upstream.getresponse()
            payload = response.read(BODY_LIMIT + 1)
            if (response.status not in ALLOWED_STATUSES or len(payload) > BODY_LIMIT
                    or response.getheader('Content-Type', '').split(';')[0].strip().lower() != 'application/json'
                    or not isinstance(json.loads(payload), dict)):
                self.error_json(502)
                return
            self.reply(response.status, payload)
        except (OSError, ValueError, http.client.HTTPException):
            self.error_json(502)
        finally:
            upstream.close()

    def do_GET(self):
        self.error_json(405 if self.path == AGENT_PATH else 404)

    do_HEAD = do_GET
    do_PUT = do_GET
    do_PATCH = do_GET
    do_DELETE = do_GET
    do_OPTIONS = do_GET


class AgentBridgeServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port, app_port, tls_context=None):
        self.app_port = app_port
        self.tls_context = tls_context
        super().__init__(('127.0.0.1', port), AgentBridgeHandler)

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(10)
        if self.tls_context is None:
            return connection, address
        try:
            return self.tls_context.wrap_socket(connection, server_side=True), address
        except OSError:
            connection.close()
            raise

    def handle_error(self, request, client_address):
        # A failed socket does not disclose request data or internal traces.
        pass


def port_number(value):
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('Use a port from 1 to 65535.') from None
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError('Use a port from 1 to 65535.')
    return port


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cert-file', required=True)
    parser.add_argument('--key-file', required=True)
    parser.add_argument('--port', type=port_number, default=8443)
    parser.add_argument('--app-port', type=port_number, default=5000)
    args = parser.parse_args()
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(args.cert_file, args.key_file)
    with AgentBridgeServer(args.port, args.app_port, context) as server:
        print(f'Agent TLS bridge listening on loopback port {args.port}.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
