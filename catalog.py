"""Desafios adicionais de investigação; conteúdo educativo, sem execução de código."""
import base64
import hashlib


def caesar(text, shift):
    result = []
    for char in text:
        if 'a' <= char <= 'z':
            char = chr((ord(char) - ord('a') + shift) % 26 + ord('a'))
        elif 'A' <= char <= 'Z':
            char = chr((ord(char) - ord('A') + shift) % 26 + ord('A'))
        result.append(char)
    return ''.join(result)


CATALOG = [
    dict(title='Cifra de César', category='Criptografia', side='Red Team', points=100,
         description='Uma mensagem foi deslocada três posições no alfabeto. Reverta o deslocamento e envie a flag completa.\n\n' + caesar('CTF{frequencia}', 3),
         hint='O prefixo FWI corresponde a CTF. Preserve chaves e caracteres que não são letras.', answer='CTF{frequencia}'),
    dict(title='Base64 em camadas', category='Criptografia', side='Blue Team', points=150,
         description='Um artefato contém duas camadas de codificação. Decodifique até encontrar a flag.\n\n' + base64.b64encode(base64.b64encode(b'CTF{camadas_nao_sao_sigilo}')).decode(),
         hint='Base64 pode representar o resultado de outra codificação Base64.', answer='CTF{camadas_nao_sao_sigilo}'),
    dict(title='Senha escondida', category='Engenharia reversa', side='Red Team', points=200,
         description='Um programa compara a entrada com caracteres representados por códigos ASCII decimais. Descubra o texto e envie CTF{texto}.\n\nconst k = [112,117,114,112,108,101,50,48,50,54];\nfunction check(s) { return s === String.fromCharCode(...k); }',
         hint='Cada número representa um caractere. Não é necessário executar o programa na plataforma.', answer='CTF{purple2026}'),
    dict(title='Cabeçalho de resposta', category='Web', side='Blue Team', points=100,
         description='Analise a resposta HTTP capturada. Qual identificador de requisição deve ser usado para correlacionar este evento com os logs? Envie CTF{identificador}.\n\nHTTP/1.1 403 Forbidden\nContent-Type: text/plain\nX-Request-ID: req-7b42\nCache-Control: no-store\n\nAccess denied',
         hint='Procure o cabeçalho que identifica a requisição, não o código de status.', answer='CTF{req-7b42}'),
    dict(title='Rastro de autenticação', category='Análise de logs', side='Blue Team', points=200,
         description='A conta deploy apresentou falhas seguidas de um acesso bem-sucedido. Identifique o IP responsável por essa sequência e envie CTF{ip}. Os endereços são fictícios, reservados para documentação.\n\n09:00 login failed user=deploy ip=192.0.2.18\n09:01 login failed user=deploy ip=192.0.2.18\n09:02 login success user=deploy ip=192.0.2.18\n09:03 login failed user=admin ip=198.51.100.9\n09:04 login success user=ana ip=203.0.113.4',
         hint='Correlacione usuário, resultado e IP; não basta procurar qualquer linha de sucesso.', answer='CTF{192.0.2.18}'),
    dict(title='Assinatura de arquivo', category='Forense', side='Blue Team', points=150,
         description='Um arquivo chamado relatorio.txt começa com os bytes hexadecimais abaixo. Qual é o tipo real do arquivo? Envie CTF{extensao}, em letras minúsculas.\n\n89 50 4E 47 0D 0A 1A 0A',
         hint='A assinatura binária é mais confiável do que a extensão fornecida no nome.', answer='CTF{png}'),
    dict(title='Permissões excessivas', category='Hardening', side='Blue Team', points=150,
         description='Um arquivo de configuração contém segredos e está com permissão 777 em Linux. Apenas seu proprietário precisa ler e escrever. Qual modo octal mínimo atende essa necessidade? Envie CTF{modo}.',
         hint='Leitura vale 4, escrita 2 e execução 1. Grupo e outros não precisam de acesso.', answer='CTF{600}'),
    dict(title='Linha do tempo do incidente', category='Resposta a incidentes', side='Blue Team', points=250,
         description='Ordene os eventos pelo horário e identifique a primeira ação defensiva após a detecção. Envie CTF{codigo}.\n\n10:06 EVT-04 restauração validada\n10:02 EVT-02 alerta de acesso incomum\n10:04 EVT-03 sessão revogada\n10:00 EVT-01 acesso inicial observado',
         hint='Detecção não é contenção. Procure a ação que interrompe o acesso após o alerta.', answer='CTF{EVT-03}'),
]


def seed_catalog(connection):
    """Insere somente títulos ausentes; nunca redefine respostas ou tentativas existentes."""
    for item in CATALOG:
        connection.execute(
            'INSERT INTO challenges(title,category,side,points,description,hint,url,flag_hash) '
            'SELECT ?,?,?,?,?,?,?,? WHERE NOT EXISTS (SELECT 1 FROM challenges WHERE title=?)',
            (item['title'], item['category'], item['side'], item['points'], item['description'],
             item['hint'], '', hashlib.sha256(item['answer'].encode()).hexdigest(), item['title']))
