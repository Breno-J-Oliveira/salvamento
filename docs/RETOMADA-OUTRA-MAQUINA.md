# Retomada em outro computador

Estado salvo em12/11/2026 após pedido de parada. Leia primeiro o início de claude.md para resultados e pendências exatas.

## Código e aplicação

```powershell
git clone https://github.com/Breno-J-Oliveira/salvamento.git
cd salvamento
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\scripts\run_local.ps1 -Demo -Port 5057
```

O launcher imprime pasta, banco e endereço. Use pasta nova ao clonar. A demonstração cria dados fictícios em banco separado. Contas de apresentação estão documentadas no roteiro existente do projeto. Para subir o banco principal use run_local.ps1 -Port5000. Este processo só deixa a plataforma disponível; o executor Linux exige os passos seguintes.

## Runtime local da VM

Caminho escolhido neste Windows foi QEMU portátil, com Ubuntu24.04 mínimo. Emulação TCG permite rodar sem instalar drivers. Avaliar aceleração e espaço no novo PC. O host anterior tinha16GB RAM e5GB livres, com reserva1200MB aplicada pelo supervisor. Os arquivos do runtime ficam em `.runtime/local-vm`, ignorados pelo Git.

Downloads usados e verificados nesta sessão:

- QEMU Windows `https://qemu.weilnetz.de/w64/qemu-w64-setup-20260811.exe`, SHA512 `5bcf9eed634e8575a37b74f445af41a2fe4106da512d0c30c368301d4c105037fdfab40a5287367a28a957624cddebbc8c07e16c88ab6634f554cdf3d16bf543`.
- Ubuntu `https://cloud-images.ubuntu.com/minimal/releases/noble/release/ubuntu-24.04-minimal-cloudimg-amd64.img`, build20261105, SHA256 `406630c08b5e545fcc7209854b129d47e3af822db128c9f19336593b5a2d3fe0`. O endereço release muda com o tempo. Se mudar o hash, obter build correspondente ou validar nova versão oficialmente antes de atualizar o pin.
- pycdlib1.14.0, wheel baixado via pip download --only-binary=:all: --no-deps, extraído em `.runtime/local-vm/tools/lib`. É ferramenta de preparaçãoISO separada do Flask. Não exige instalar no ambiente do produto.

Extrair com7-Zip os executáveis qemu-system-x86_64.exe e qemu-img.exe, DLLs e os arquivos share/bios*.bin, share/vgabios*.bin, share/kvmvapic.bin, share/efi-virtio.rom e share/linuxboot*.bin para `.runtime/local-vm/qemu`. O instalador não foi executado. Manter licenças disponíveis e usar as fontes oficiais referenciadas no runbook.

Criar certificado local novo e chave privada para a ponte, com SAN IP10.0.2.100 e127.0.0.1. Nesta sessão foi usado OpenSSL do Git for Windows:

```powershell
openssl req -x509 -newkey rsa:2048 -nodes -keyout .runtime/local-vm/bridge.key -out .runtime/local-vm/bridge.crt -days 30 -subj '/CN=Purple Local Lab' -addext 'subjectAltName=IP:10.0.2.100,IP:127.0.0.1'
```

Antes de gerar tokens, restringir ACL da pasta runtime ao operador e SYSTEM. Se transferir os binários/imagem-base deste PC, verificar novamente os hashes. Criar certificados e tokens novos. Overlays aposentados, seeds antigos e arquivos de credencial são históricos privados, não modelos reutilizáveis.

## Conectar um executor novo

Com aplicação demo5057 aberta, iniciar em outro terminal:

```powershell
.\.venv\Scripts\python.exe scripts/lab_tls_bridge.py --cert-file .runtime/local-vm/bridge.crt --key-file .runtime/local-vm/bridge.key --app-port 5057
.\.venv\Scripts\python.exe scripts/prepare_local_vm.py --database output/demo/presentation.demo.db > .runtime/local-vm/current.json
.\.venv\Scripts\python.exe scripts/run_local_vm.py --metadata .runtime/local-vm/current.json
```

A ponte permanece aberta no próprio terminal. Usar um terceiro terminal para preparar e supervisionar a VM. Esperar o agente na tela5057/remote-labs. A reserva confirma contato recente. Validar id -u, id -Gn, systemd-detect-virt e cat access.log. Conferir a sessão no perfil mentor. O resultado é mostrado após cada comando, sem PTY ou desktop remoto.

Para disponibilizar no principal5000, encerrar o ensaio, aguardar desligamento da VM e da ponte, iniciar nova ponte com app-port5000 e preparar novo cadastro com --database lab.db. Sempre gerar novo JSON/seed/overlay. A máquinaDEMO id1 anterior está aposentada. Nenhum executor principal foi criado antes da parada.

## Arquivos privados e limites

Para migrar dados existentes, preservar lab.db e .session-key da versão correta por canal privado. Copiar com o servidor parado e fazer backup antes de qualquer restauração. A .venv deve ser recriada. O diretório `.runtime/local-vm` e output não são obtidos com git clone. As evidências sintéticas podem ser copiadas separadamente se necessárias.

Persistem como trabalho futuro um instalador verificado de runtime, comandos únicos de iniciar/recriar, criação automática pelo site, interface para mais de um desafio/VM, terminal interativo, políticas de retenção e publicação HTTPS online. A ponte local8443 expõe somente a API do agente em loopback e não representa hospedagem pública.
