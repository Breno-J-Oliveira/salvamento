# Constrói a VM base "cti-lab-base" e o snapshot "base" usados pelo orchestrator.py.
# Uso (na raiz do projeto):  powershell -ExecutionPolicy Bypass -File scripts\setup_virtualbox.ps1 [-Rebuild]
param([switch]$Rebuild)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$vmDir = Join-Path $root 'vm'
$vbox = Join-Path ${env:ProgramFiles} 'Oracle\VirtualBox\VBoxManage.exe'
if (-not (Test-Path $vbox)) { throw 'VirtualBox não encontrado. Instale com: winget install -e --id Oracle.VirtualBox' }
if (-not (Get-Command vagrant -ErrorAction SilentlyContinue)) {
    $env:Path += ';C:\Program Files\Vagrant\bin;C:\HashiCorp\Vagrant\bin'
    if (-not (Get-Command vagrant -ErrorAction SilentlyContinue)) { throw 'Vagrant não encontrado. Instale com: winget install -e --id Hashicorp.Vagrant' }
}
Push-Location $vmDir
try {
    if ($Rebuild) {
        & $vbox list vms | Select-String '"(lab-u\d+-c\d+-[0-9a-f]+)"' | ForEach-Object {
            $n = $_.Matches[0].Groups[1].Value
            & $vbox controlvm $n poweroff 2>$null; & $vbox unregistervm $n --delete
        }
        vagrant destroy -f
    }
    vagrant up --provider virtualbox
    if ($LASTEXITCODE) { throw 'vagrant up falhou' }
    vagrant halt
    # Remove o encaminhamento SSH do Vagrant: clones não devem expor nenhuma porta além do desafio.
    & $vbox showvminfo cti-lab-base --machinereadable | Select-String '^Forwarding\(\d+\)="([^,]+),' | ForEach-Object {
        & $vbox modifyvm cti-lab-base --natpf1 delete $_.Matches[0].Groups[1].Value
    }
    & $vbox snapshot cti-lab-base list --machinereadable 2>$null | Select-String 'SnapshotName.*="base"' | ForEach-Object {
        & $vbox snapshot cti-lab-base delete base
    }
    & $vbox snapshot cti-lab-base take base --description 'Base dos laboratórios CTI'
    Write-Host 'VM base pronta: cti-lab-base (snapshot "base").'
} finally { Pop-Location }
