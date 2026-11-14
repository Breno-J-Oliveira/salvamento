# Hospedagem gratuita do Purple Talent

Use o plano gratuito do PythonAnywhere para uma demonstração. Ele oferece HTTPS e armazenamento persistente. Na consulta, o plano incluía 512 MiB, um processo web e validade de um mês. Confira as condições atuais.

O SQLite atenderá candidatos e mentor pelo mesmo site. Os desafios que dependem de VirtualBox/Vagrant estão bloqueados em produção até haver infraestrutura compatível. Algumas respostas de CTF estão no código público. A empresa deve avaliar segurança e disponibilidade antes de receber dados reais.

## 1. Criar conta e baixar o projeto

Crie uma conta em https://www.pythonanywhere.com/, abra Consoles, inicie um console Bash e execute:

~~~bash
cd ~
git clone https://github.com/Breno-J-Oliveira/CTI-PurpleTalent.git purple-talent
cd ~/purple-talent
mkvirtualenv --python=/usr/bin/python3.12 purple-talent
pip install -r requirements.txt
~~~

Selecione a mesma versão Python na criação do aplicativo. Confira o espaço na aba Files.

## 2. Criar configuração privada e banco

Execute abaixo. Informe o domínio sem https:// e escolha uma senha forte de mentoria. Ela não aparece na tela.

~~~bash
mkdir -p ~/purple-private
chmod 700 ~/purple-private
python - <<'PY'
from getpass import getpass
from pathlib import Path
import json, os, secrets

home = Path.home()
path = home / "purple-private" / "settings.json"
if path.exists():
    raise SystemExit("Configuração já existe. Preserve-a.")
host = input("Domínio sem https://: ").strip().lower()
password = getpass("Senha inicial do mentor, mínimo 12 caracteres: ")
if not host or "/" in host or ":" in host or len(password) < 12:
    raise SystemExit("Domínio ou senha inválidos.")
settings = {
    "PURPLE_ENV": "production",
    "LAB_DATABASE": str(home / "purple-private" / "lab.db"),
    "SECRET_KEY": secrets.token_hex(32),
    "ALLOWED_HOSTS": host,
    "MENTOR_PASSWORD": password,
}
fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
with os.fdopen(fd, "w", encoding="utf-8") as file:
    json.dump(settings, file)
print("Configuração criada.")
PY
~~~

Inicialize o banco, preservando dados existentes:

~~~bash
cd ~/purple-talent
workon purple-talent
python - <<'PY'
from pathlib import Path
import json, os
os.environ.update(json.loads((Path.home() / "purple-private" / "settings.json").read_text()))
from app import init_db
init_db()
print("Banco inicializado.")
PY
~~~

O usuário inicial de mentoria é mentor@cti.local, com a senha escolhida. Banco e chave ficam fora do repositório. Mantenha o PDF de gabarito privado.

## 3. Configurar o aplicativo web

1. Na aba Web escolha Add a new web app, depois Manual configuration e a mesma versão Python do ambiente virtual.
2. Na seção Virtualenv informe /home/SEU_USUARIO/.virtualenvs/purple-talent, trocando SEU_USUARIO.
3. Na seção Code ajuste o diretório para /home/SEU_USUARIO/purple-talent.
4. Abra WSGI configuration file e substitua o conteúdo abaixo, trocando SEU_USUARIO:

~~~python
import json
import os
import sys
from pathlib import Path

home = Path("/home/SEU_USUARIO")
os.environ.update(json.loads((home / "purple-private" / "settings.json").read_text(encoding="utf-8")))
sys.path.insert(0, str(home / "purple-talent"))
from app import app as application
~~~

5. Clique em Reload e abra https://SEU_USUARIO.pythonanywhere.com. Consulte Error log se houver erro.

O WSGI usa o servidor do PythonAnywhere. O script start_production.py pertence ao procedimento do Render.

## 4. Verificar e manter

- Cadastre uma pessoa fictícia em um navegador e entre como mentor em outro computador. Confira equipes, candidatura e respostas.
- Faça Reload, entre novamente e confirme que os registros continuam salvos.
- Para atualizar, faça backup, execute git pull --ff-only na pasta ~/purple-talent, reinstale as dependências, execute a inicialização do passo 2 e clique em Reload.
- Use scripts/backup_database.py para criar cópia em destino novo e teste a restauração em outro arquivo. Guarde cópias privadas fora da hospedagem.
- Acompanhe o espaço e renove o aplicativo quando solicitado. Um único processo pode gerar espera para acessos simultâneos.
- Teste a configuração de proxy e proteção dos dados na conta escolhida antes de receber dados reais.

## Para a próxima IA

Valide a implantação na conta autorizada, proxy, autenticação, CSRF, HTTPS, limites, isolamento das respostas, persistência após Reload e restauração de backup. Planeje a execução segura das VMs e substitua respostas fixas de CTF para uma seleção sigilosa. Não publique bancos, chaves ou gabaritos.

Fontes: https://help.pythonanywhere.com/pages/FreeAccountsFeatures, https://help.pythonanywhere.com/pages/Flask e https://help.pythonanywhere.com/pages/DiskQuota.
