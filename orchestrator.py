"""Ambientes Docker locais. Apenas imagens e containers deste projeto são aceitos."""
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
NETWORK = "cti-lab-net"
LABEL = "cti-lab=1"
IMAGE_DIRS = {"cti-lab/web-01": os.path.join(BASE, "challenges", "web-01")}
NAME = re.compile(r"lab-u[0-9]+-c[0-9]+-[a-f0-9]{6,32}\Z")


class DockerError(Exception):
    pass


def _docker(*args, timeout=60, env=None):
    try:
        result = subprocess.run(["docker", *args], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=timeout, env=env)
    except FileNotFoundError as error:
        raise DockerError("Docker não encontrado. Instale e abra o Docker Desktop.") from error
    except subprocess.TimeoutExpired as error:
        raise DockerError("O Docker demorou demais para responder. Verifique o Docker Desktop.") from error
    if result.returncode:
        # Docker can echo flags, environment values and host paths in errors.
        raise DockerError("O Docker não concluiu a operação. Verifique se o Docker Desktop está ativo.")
    return result.stdout.strip()


def ensure_network():
    names = _docker("network", "ls", "--filter", f"name=^{NETWORK}$", "--format", "{{.Name}}")
    if NETWORK not in names.splitlines():
        _docker("network", "create", "--driver", "bridge", "--label", LABEL,
                "-o", "com.docker.network.bridge.enable_icc=false", NETWORK)
    network = json.loads(_docker("network", "inspect", NETWORK))[0]
    if network.get("Options", {}).get("com.docker.network.bridge.enable_icc") != "false":
        raise DockerError("A rede do laboratório não está isolada. Revise a configuração da rede cti-lab-net.")


def ensure_image(image):
    if image not in IMAGE_DIRS:
        raise DockerError("Imagem de laboratório não permitida.")
    images = _docker("image", "ls", "--filter", f"reference={image}", "--format", "{{.ID}}")
    if not images:
        _docker("build", "-t", image, IMAGE_DIRS[image], timeout=600)


def _validate_name(name):
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise DockerError("Identificador de ambiente inválido.")


def _owned_names():
    return _docker("ps", "-a", "--filter", f"label={LABEL}", "--format", "{{.Names}}").splitlines()


def status(name):
    _validate_name(name)
    names = _docker("ps", "--filter", f"label={LABEL}", "--format", "{{.Names}}", timeout=5)
    return name in names.splitlines()


def stop(name):
    """Ausência é idempotente; falhas reais não podem ser registradas como sucesso."""
    _validate_name(name)
    if name in _owned_names():
        _docker("rm", "-f", name)


def start(name, image, container_port, flag):
    _validate_name(name)
    if image not in IMAGE_DIRS or container_port != 5000:
        raise DockerError("Configuração de laboratório não permitida.")
    if not isinstance(flag, str) or not re.fullmatch(r"CTF\{[a-f0-9]{16,64}\}", flag):
        raise DockerError("Configuração de flag inválida.")
    ensure_network()
    ensure_image(image)
    env = os.environ.copy()
    env["FLAG"] = flag
    # Docker chooses the free port atomically. The secret is not in process arguments.
    _docker("run", "-d", "--rm", "--name", name, "--label", LABEL, "--network", NETWORK,
            "-p", "127.0.0.1::5000", "-e", "FLAG", "--memory", "128m", "--cpus", "0.5",
            "--pids-limit", "64", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m", image, env=env)
    try:
        mapping = json.loads(_docker("inspect", "--format", "{{json .NetworkSettings.Ports}}", name))
        binding = mapping["5000/tcp"][0]
        if binding["HostIp"] != "127.0.0.1":
            raise DockerError("O ambiente não recebeu uma porta local segura.")
        port = int(binding["HostPort"])
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as response:
                    if response.status == 200:
                        return port
            except (urllib.error.URLError, TimeoutError, OSError):
                time.sleep(0.25)
        raise DockerError("O laboratório não ficou pronto. Tente iniciar novamente.")
    except (KeyError, IndexError, ValueError, TypeError) as error:
        stop(name)
        raise DockerError("O Docker retornou uma configuração de porta inválida.") from error
    except Exception:
        stop(name)
        raise


def cleanup_all():
    """Limpeza explícita; não executar automaticamente em toda inicialização."""
    for name in _owned_names():
        if NAME.fullmatch(name):
            stop(name)


