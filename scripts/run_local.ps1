[CmdletBinding()]
param(
    [switch]$Demo,
    [string]$Database,
    [ValidateRange(1, 65535)][int]$Port = 5000
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$python = $null
$searchRoot = $projectRoot
while ($searchRoot) {
    $candidatePython = Join-Path $searchRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $candidatePython -PathType Leaf) {
        $python = $candidatePython
        break
    }
    $parentRoot = Split-Path -Parent $searchRoot
    if ($parentRoot -eq $searchRoot) { break }
    $searchRoot = $parentRoot
}
if (-not $python) {
    throw 'Python da .venv não encontrado nesta pasta ou nos ancestrais. Prepare a .venv conforme README.md.'
}
& $python -c 'import flask, importlib.metadata; print("Flask " + importlib.metadata.version("Flask"))'
if ($LASTEXITCODE -ne 0) {
    throw "Dependências indisponíveis. Execute: & '$python' -m pip install -r '$projectRoot\requirements.txt'"
}

if (-not $Database) {
    $Database = if ($Demo) { Join-Path $projectRoot 'output\demo\presentation.demo.db' } else { Join-Path $projectRoot 'lab.db' }
} elseif (-not [IO.Path]::IsPathRooted($Database)) {
    $Database = Join-Path $projectRoot $Database
}
$databasePath = [IO.Path]::GetFullPath($Database)

# Verifica disponibilidade sem interromper ou substituir qualquer processo existente.
$probe = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $Port)
try { $probe.Start() }
catch { throw "A porta $Port está ocupada ou indisponível. Escolha outra com -Port; nenhum processo foi encerrado." }
finally { $probe.Stop() }

if ($Demo) {
    if ([IO.Path]::GetFileName($databasePath) -ieq 'lab.db') {
        throw 'O modo Demo não aceita lab.db. Escolha outro arquivo com -Database.'
    }
    if (Test-Path -LiteralPath $databasePath) {
        & $python -c 'import sqlite3, sys; from pathlib import Path; p=Path(sys.argv[1]).resolve(); c=sqlite3.connect(p.as_uri()+"?mode=ro", uri=True); assert c.execute("SELECT value FROM demo_metadata WHERE name=?", ("fixture",)).fetchone()==("purple-talent-presentation-v1",), "Banco sem marcador de demonstracao"; c.close()' $databasePath
        if ($LASTEXITCODE -ne 0) { throw 'Este arquivo não é uma base de demonstração reconhecida. Nenhuma alteração foi aplicada.' }
    } else {
        & $python (Join-Path $PSScriptRoot 'prepare_demo.py') $databasePath
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível preparar a demonstração.' }
    }
}

$revision = 'sem metadados Git'
if (Get-Command git -ErrorAction SilentlyContinue) {
    try {
        $gitRevision = & git -C $projectRoot rev-parse --short HEAD 2>$null
        if ($LASTEXITCODE -eq 0) { $revision = $gitRevision }
    } catch { $revision = 'sem metadados Git' }
}
Write-Host "Projeto: $projectRoot"
Write-Host "Commit: $revision (alterações locais podem existir)"
Write-Host "Python: $python"
Write-Host "Modo: $(if ($Demo) { 'DEMONSTRAÇÃO — dados fictícios, sem VirtualBox no percurso principal' } else { 'LOCAL — banco selecionado abaixo' })"
Write-Host "Banco: $databasePath"
Write-Host "Endereço: http://127.0.0.1:$Port"
Write-Host 'Ctrl+C encerra este servidor. Nenhum processo existente será encerrado pelo launcher.'

$oldDatabase = $env:LAB_DATABASE
$oldPort = $env:PORT
$oldKey = $env:SECRET_KEY
try {
    $env:LAB_DATABASE = $databasePath
    $env:PORT = [string]$Port
    # Demo tem sessão efêmera independente da chave/banco da equipe.
    if ($Demo) { $env:SECRET_KEY = [Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N') }
    & $python (Join-Path $projectRoot 'app.py')
    if ($LASTEXITCODE -ne 0) { throw "Servidor encerrou com código $LASTEXITCODE." }
} finally {
    $env:LAB_DATABASE = $oldDatabase
    $env:PORT = $oldPort
    $env:SECRET_KEY = $oldKey
}
