# Ambientes virtuais VirtualBox

A aplicação Flask roda no computador local e cria uma máquina virtual VirtualBox para cada participante que inicia um desafio com ambiente. O SQLite permanece no host; as VMs não recebem o banco, o código da plataforma nem pastas compartilhadas.

## Instalar

```powershell
winget install -e --id Oracle.VirtualBox
winget install -e --id Hashicorp.Vagrant
```

Feche e reabra o terminal depois da instalação para atualizar o `PATH`.

## Criar a VM base (uma vez)

Na raiz do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_virtualbox.ps1
```

O script usa o Vagrant (`vm/Vagrantfile`) para baixar a box `bento/ubuntu-24.04`, instalar Python/Flask, copiar `challenges/web-01` e `challenges/incident-01` para `/opt/cti-lab` e registrar o serviço `cti-lab`. Em seguida desliga a VM, remove o encaminhamento SSH e tira o snapshot `base` da VM `cti-lab-base`.

Depois de alterar um desafio, reconstrua com `-Rebuild` (remove também as instâncias `lab-u*` existentes).

## Como uma instância funciona

1. `orchestrator.start` cria um clone vinculado (`clonevm --options link`) do snapshot `base`, no grupo `/cti-lab`, marcado com o extradata `cti-lab/owner=1`.
2. Configura 512 MiB, 1 CPU com teto de 50%, NAT própria e um encaminhamento `127.0.0.1:<porta livre> → 5000`.
3. Grava o desafio e a flag como guest properties `RDONLYGUEST` (`/CTI/Challenge`, `/CTI/Flag`). A flag não aparece em argumentos de processos do convidado.
4. Inicia a VM em modo headless e só libera o endereço quando `/health` responder (até 4 minutos).
5. Dentro da VM, `run.sh` lê as propriedades e executa o desafio como usuário `ctf`, sem privilégios, com limites de memória (128 MiB), processos (64) e CPU via systemd.

`orchestrator.stop` desliga e apaga (`unregistervm --delete`) somente VMs com nome `lab-u…-c…-…` e o marcador de dono.

## Verificação

```powershell
python -m unittest discover -s tests -v
$env:RUN_VBOX_TESTS = '1'
python -m unittest discover -s tests -p "test_orchestrator.py" -v
python -m unittest discover -s tests -p "test_incident_vbox.py" -v
Remove-Item Env:RUN_VBOX_TESTS
```

## Limites

- Uso local: os endereços `127.0.0.1` não são acessíveis de outra máquina.
- Cada VM leva de 30 s a 2 min para iniciar; a requisição de "Iniciar ambiente" aguarda esse tempo.
- Com `MAX_ACTIVE = 10`, o pior caso usa cerca de 5 GiB de RAM. Reduza em `app.py` se o computador tiver pouca memória.
- Se o Hyper-V/WSL2 estiver ativo, o VirtualBox roda sobre a API do Hyper-V e fica mais lento.
- A NAT do VirtualBox permite saída para a internet; ela impede apenas acesso entre instâncias e ao localhost do host (`--nat-localhostreachable1 off`).
