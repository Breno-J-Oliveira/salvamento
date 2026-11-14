"""Ambientes VirtualBox locais. Apenas máquinas virtuais deste projeto são aceitas.

Cada instância é um clone vinculado (linked clone) da VM base ``cti-lab-base``,
criada uma única vez por ``scripts/setup_virtualbox.ps1``. A flag e o desafio são
entregues ao convidado por guest properties somente leitura, nunca por argumentos
de linha de comando visíveis no host.
"""
import logging
import os
import re
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
BASE_VM = "cti-lab-base"
BASE_SNAPSHOT = "base"
GROUP = "/cti-lab"
OWNER_KEY = "cti-lab/owner"
IMAGES = {"cti-lab/web-01": "web-01", "cti-lab/incident-01": "incident-01"}
NAME = re.compile(r"lab-u[0-9]+-c[0-9]+-[a-f0-9]{6,32}\Z")
QUERY_TIMEOUT = 15
STOP_TIMEOUT = 60
READY_TIMEOUT = 240
VM_MEMORY_MB = 512
VM_CPUS = 1
logger = logging.getLogger(__name__)


class LabError(Exception):
    pass


# Nome antigo mantido para compatibilidade com app.py e testes existentes.
DockerError = LabError


def _vboxmanage_path():
    found = shutil.which("VBoxManage")
    if found:
        return found
    for root in (os.environ.get("VBOX_MSI_INSTALL_PATH"), os.environ.get("VBOX_INSTALL_PATH"),
                 r"C:\Program Files\Oracle\VirtualBox"):
        if root:
            candidate = os.path.join(root, "VBoxManage.exe")
            if os.path.isfile(candidate):
                return candidate
    return "VBoxManage"


def _vbox(*args, timeout=60):
    try:
        result = subprocess.run([_vboxmanage_path(), *args], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=timeout)
    except FileNotFoundError as error:
        raise LabError("VirtualBox não encontrado. Instale o VirtualBox e execute scripts/setup_virtualbox.ps1.") from error
    except subprocess.TimeoutExpired as error:
        raise LabError("O VirtualBox demorou demais para responder.") from error
    except OSError as error:
        raise LabError("Não foi possível executar o VirtualBox neste computador.") from error
    if result.returncode:
        # VBoxManage pode ecoar caminhos do host e valores de propriedades em erros.
        raise LabError("O VirtualBox não concluiu a operação.")
    return result.stdout.strip()


def _vm_names(command):
    names = []
    for line in _vbox("list", command, timeout=QUERY_TIMEOUT).splitlines():
        match = re.match(r'"(.*)" \{[0-9a-fA-F-]+\}\s*$', line)
        if match:
            names.append(match.group(1))
    return names


def ensure_base():
    if BASE_VM not in _vm_names("vms"):
        raise LabError("VM base do laboratório ausente. Execute scripts/setup_virtualbox.ps1.")
    snapshots = _vbox("snapshot", BASE_VM, "list", "--machinereadable", timeout=QUERY_TIMEOUT)
    if f'="{BASE_SNAPSHOT}"' not in snapshots:
        raise LabError("Snapshot base do laboratório ausente. Execute scripts/setup_virtualbox.ps1.")


def ensure_image(image):
    """Compatibilidade: valida o desafio e garante que a VM base existe."""
    if image not in IMAGES:
        raise LabError("Imagem de laboratório não permitida.")
    ensure_base()


def _validate_name(name):
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise LabError("Identificador de ambiente inválido.")


def _is_owned(name):
    if name not in _vm_names("vms"):
        return False
    value = _vbox("getextradata", name, OWNER_KEY, timeout=QUERY_TIMEOUT)
    return value.strip() == "Value: 1"


def _owned_names():
    return [n for n in _vm_names("vms") if NAME.fullmatch(n) and _is_owned(n)]


def status(name):
    _validate_name(name)
    return name in _vm_names("runningvms")


def stop(name):
    """Ausência é idempotente; falhas reais não podem ser registradas como sucesso."""
    _validate_name(name)
    if not _is_owned(name):
        return
    if name in _vm_names("runningvms"):
        _vbox("controlvm", name, "poweroff", timeout=STOP_TIMEOUT)
    # A sessão da VM pode levar alguns segundos para ser liberada após o poweroff.
    last = None
    for _ in range(10):
        try:
            _vbox("unregistervm", name, "--delete", timeout=STOP_TIMEOUT)
            return
        except LabError as error:
            last = error
            time.sleep(1)
    raise last


def _cleanup_failed_start(name, original):
    """Tenta recuperar a instância criada sem substituir o erro de inicialização."""
    try:
        stop(name)
    except LabError:
        original.add_note("A limpeza do ambiente também falhou; a instância pode precisar de reconciliação.")
        logger.warning("Não foi possível limpar ambiente após falha de inicialização")


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start(name, image, container_port, flag):
    _validate_name(name)
    if image not in IMAGES or container_port != 5000:
        raise LabError("Configuração de laboratório não permitida.")
    if not isinstance(flag, str) or not re.fullmatch(r"CTF\{[a-f0-9]{16,64}\}", flag):
        raise LabError("Configuração de flag inválida.")
    ensure_image(image)
    _vbox("clonevm", BASE_VM, "--snapshot", BASE_SNAPSHOT, "--options", "link",
          "--name", name, "--groups", GROUP, "--register", timeout=STOP_TIMEOUT)
    try:
        _vbox("setextradata", name, OWNER_KEY, "1", timeout=QUERY_TIMEOUT)
        port = _free_port()
        # NAT própria por VM: as instâncias não se enxergam. A porta só escuta em 127.0.0.1.
        _vbox("modifyvm", name, "--memory", str(VM_MEMORY_MB), "--cpus", str(VM_CPUS),
              "--cpuexecutioncap", "50", "--nic1", "nat", timeout=QUERY_TIMEOUT)
        _vbox("modifyvm", name, "--natpf1", f"lab,tcp,127.0.0.1,{port},,5000",
              "--nat-localhostreachable1", "off", timeout=QUERY_TIMEOUT)
        _vbox("guestproperty", "set", name, "/CTI/Challenge", IMAGES[image], "--flags", "RDONLYGUEST",
              timeout=QUERY_TIMEOUT)
        _vbox("guestproperty", "set", name, "/CTI/Flag", flag, "--flags", "RDONLYGUEST",
              timeout=QUERY_TIMEOUT)
        _vbox("startvm", name, "--type", "headless", timeout=STOP_TIMEOUT)
        deadline = time.monotonic() + READY_TIMEOUT
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as response:
                    if response.status == 200:
                        return port
            except (urllib.error.URLError, TimeoutError, OSError):
                time.sleep(1)
        raise LabError("O laboratório não ficou pronto. Tente iniciar novamente.")
    except Exception as error:
        _cleanup_failed_start(name, error)
        raise


def cleanup_all():
    """Limpeza explícita; não executar automaticamente em toda inicialização."""
    for name in _owned_names():
        stop(name)
