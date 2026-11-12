"""Disposable Linux VM supervisor. Commands run as a separate unprivileged UID.

This program requires an actual isolated lab machine. It does not create a VM.
The service token belongs to root and must never be copied into the lab workspace.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import selectors
import signal
import stat
import ssl
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from urllib.parse import urlsplit

OUTPUT_LIMIT = 16000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, 'Redirect refused', headers, fp)


def api_url(base, allow_local_http=False):
    parsed = urlsplit(base)
    local = parsed.hostname in ('localhost', '127.0.0.1', '::1')
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Use a server URL without credentials, query or fragment.')
    if parsed.path not in ('', '/') or not parsed.hostname:
        raise ValueError('Use the server origin, without a path.')
    if parsed.scheme != 'https' and not (allow_local_http and local and parsed.scheme == 'http'):
        raise ValueError('HTTPS is required. Local HTTP is available only for local QA.')
    return base.rstrip('/') + '/api/lab-agent/poll'


def read_token(path):
    secret = Path(path)
    if secret.is_symlink() or not secret.is_file():
        raise ValueError('Token must be a regular file.')
    info = secret.stat()
    if platform.system() == 'Linux':
        if info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError('Token must belong to root and have mode 0600 or 0400.')
        parent = secret.parent.stat()
        if parent.st_uid != 0 or stat.S_IMODE(parent.st_mode) & 0o022:
            raise ValueError('Token directory must belong to root and disallow other writers.')
    token = secret.read_text(encoding='utf-8').strip()
    if len(token) < 32 or len(token) > 256 or not token.isascii() or any(c.isspace() for c in token):
        raise ValueError('Invalid token file.')
    return token


def execution_identity(run_as, workspace, isolated):
    if platform.system() != 'Linux' or not isolated:
        raise ValueError('Execution requires Linux and --isolated-lab inside a disposable VM.')
    if os.geteuid() != 0:
        raise ValueError('The supervisor must run as root; commands run under --run-as.')
    if (not Path('/run/systemd/system').is_dir() or
            not Path('/usr/bin/systemd-run').is_file() or
            not Path('/usr/bin/systemctl').is_file()):
        raise ValueError('A Linux VM with running systemd is required for command isolation.')
    require_systemd_version()
    import pwd
    import grp
    try:
        identity = pwd.getpwnam(run_as)
    except KeyError:
        raise ValueError('The execution account does not exist.') from None
    if identity.pw_uid < 1000 or identity.pw_gid < 1000:
        raise ValueError('Use a dedicated account with UID and GID of at least 1000.')
    try:
        primary = grp.getgrgid(identity.pw_gid)
    except KeyError:
        raise ValueError('The execution primary group does not exist.') from None
    if primary.gr_name != run_as or set(primary.gr_mem) - {run_as}:
        raise ValueError('The execution account requires its own dedicated primary group.')
    if set(os.getgrouplist(run_as, identity.pw_gid)) != {identity.pw_gid}:
        raise ValueError('The execution account must have only its primary group, without sudo or privileged groups.')
    folder = Path(workspace)
    if not folder.is_absolute() or not folder.is_dir() or folder.is_symlink() or '%' in str(folder):
        raise ValueError('Workspace must be an existing absolute directory.')
    folder = folder.resolve()
    if folder.stat().st_uid != identity.pw_uid:
        raise ValueError('Workspace must belong to the execution account.')
    # Avoid inheriting privileged supplementary groups and service environment.
    return identity, folder


def require_systemd_version():
    try:
        version = subprocess.run(['/usr/bin/systemd-run', '--version'],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, timeout=5, check=True, text=True)
    except (OSError, subprocess.SubprocessError):
        raise ValueError('Cannot verify systemd version.') from None
    match = re.match(r'systemd ([0-9]{1,6})\b', version.stdout)
    if not match or int(match.group(1)) < 254:
        raise ValueError('systemd 254 or newer is required. Use Ubuntu 24.04 or a compatible VM.')


def service_command(command, identity, workspace, timeout, unit):
    """Every shell belongs to a bounded systemd cgroup, including setsid children."""
    return ['/usr/bin/systemd-run', '--quiet', '--wait', '--pipe', '--collect',
            '--expand-environment=no',
            '--service-type=exec', '--unit=' + unit,
            '--property=User=' + str(identity.pw_uid),
            '--property=Group=' + str(identity.pw_gid),
            '--property=SupplementaryGroups=',
            '--property=NoNewPrivileges=yes', '--property=CapabilityBoundingSet=',
            '--property=RestrictSUIDSGID=yes', '--property=KillMode=control-group',
            '--property=MemoryMax=256M', '--property=TasksMax=64',
            '--property=CPUQuota=100%', '--property=PrivateTmp=yes',
            '--property=RuntimeMaxSec=' + str(timeout), '--property=TimeoutStopSec=2',
            '--property=WorkingDirectory=' + str(workspace),
            '--setenv=PATH=/usr/local/bin:/usr/bin:/bin',
            '--setenv=HOME=' + str(workspace), '--setenv=LANG=C.UTF-8',
            '/bin/sh', '-c', command]


def stop_service(unit):
    stopped = False
    try:
        result = subprocess.run(['/usr/bin/systemctl', 'stop', unit], stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False)
        stopped = result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        pass
    if not stopped:
        subprocess.run(['/usr/bin/systemctl', 'kill', '--signal=KILL', unit],
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=5, check=False)


def format_output(output, truncated=False, expired=False):
    suffix = '\n[Saída limitada a 16 KB.]' if truncated else ''
    if expired:
        suffix += '\n[Tempo de execução encerrado.]'
    text = output.decode('utf-8', errors='replace').replace('\x00', '\ufffd')
    return text[:OUTPUT_LIMIT-len(suffix)] + suffix


def execute_job(job, expires_at, identity, workspace):
    """Run once, bound output in memory, stop the complete service cgroup."""
    command = job.get('command')
    if not isinstance(command, str) or not 1 <= len(command) <= 1000 or '\x00' in command:
        raise ValueError('Invalid command.')
    timeout = min(25, max(1, int(job.get('timeout', 25))))
    remaining = min(timeout, expires_at - time.time())
    if remaining <= 0:
        return {'command_id': job['command_id'], 'lease_token': job['lease_token'],
                'output': 'A sessão expirou antes da execução.', 'exit_code': 124}
    unit = 'purple-lab-' + uuid.uuid4().hex + '.service'
    process = subprocess.Popen(
        service_command(command, identity, workspace, remaining, unit), cwd='/',
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        start_new_session=True, umask=0o077,
        env={'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/root',
             'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'})
    output = bytearray()
    truncated = False
    expired = False
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    deadline = time.monotonic() + remaining
    try:
        while True:
            if process.poll() is not None:
                # Background children must not survive their command shell.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            wait = deadline - time.monotonic()
            if wait <= 0:
                expired = True
                break
            events = selector.select(min(wait, 0.1))
            for key, _ in events:
                chunk = os.read(key.fileobj.fileno(), 8192)
                if not chunk:
                    selector.unregister(key.fileobj)
                    break
                room = OUTPUT_LIMIT - len(output)
                output.extend(chunk[:room])
                truncated = truncated or len(chunk) > room
            if not selector.get_map():
                try:
                    process.wait(timeout=max(0.01, deadline-time.monotonic()))
                except subprocess.TimeoutExpired:
                    expired = True
                break
    finally:
        stop_service(unit)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)
        selector.close()
        process.stdout.close()
    return {'command_id': job['command_id'], 'lease_token': job['lease_token'],
            'output': format_output(output, truncated, expired),
            'exit_code': 124 if expired else process.returncode}


def poll(opener, url, token, result):
    payload = json.dumps({'result': result}, ensure_ascii=False).encode('utf-8', errors='replace')
    request = urllib.request.Request(url, data=payload,
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}, method='POST')
    with opener.open(request, timeout=15) as response:
        body = response.read(65537)
    if len(body) > 65536:
        raise ValueError('Server response exceeded its size limit.')
    reply = json.loads(body)
    if not isinstance(reply, dict) or reply.get('state') not in ('idle', 'active', 'retired'):
        raise ValueError('Invalid server reply.')
    return reply


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', required=True)
    parser.add_argument('--token-file', required=True)
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--run-as', required=True)
    parser.add_argument('--isolated-lab', action='store_true')
    parser.add_argument('--allow-local-http', action='store_true')
    parser.add_argument('--ca-file', help='Additional trusted CA for a private HTTPS lab gateway.')
    args = parser.parse_args()
    try:
        identity, workspace = execution_identity(args.run_as, args.workspace, args.isolated_lab)
        url = api_url(args.server, args.allow_local_http)
        token = read_token(args.token_file)
    except ValueError as exc:
        parser.error(str(exc))
    print('Agente ativo em VM descartável com systemd. Use conta de execução sem sudo e sem credenciais pessoais.', flush=True)
    # One-use commands remain remembered for the life of this disposable VM.
    results = {}
    pending = None
    context = ssl.create_default_context(cafile=args.ca_file)
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))
    while True:
        try:
            reply = poll(opener, url, token, pending)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            print('Conexão indisponível. Reenvio pendente preservado.', flush=True)
            time.sleep(2)
            continue
        pending = None
        if reply['state'] == 'retired':
            print('Máquina retirada do conjunto. Recrie a VM antes de uma nova sessão.', flush=True)
            return
        job = reply.get('job')
        if job is not None:
            identifier = job.get('command_id')
            lease = job.get('lease_token')
            expires = reply.get('expires_at')
            if (type(identifier) is not int or not isinstance(lease, str) or
                    not 16 <= len(lease) <= 256 or type(expires) is not int):
                raise SystemExit('Contrato de execução inválido. Agente encerrado.')
            key = (identifier, lease)
            if key not in results:
                if len(results) >= 200:
                    raise SystemExit('Limite de comandos atingido. Agente encerrado.')
                results[key] = execute_job(job, expires, identity, workspace)
            pending = results[key]
        time.sleep(2)


if __name__ == '__main__':
    main()
