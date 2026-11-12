# Revisão de segurança e recuperação para apresentação

Revisão de 11/11/2026, dirigida à aplicação local e ao fluxo de recrutamento. O resultado não equivale a certificação de segurança nem autorização para exposição pública.

## Proteções acrescentadas

1. **Host local — risco médio corrigido.** A aplicação aceitava nomes de host arbitrários. `app.py:42`, função `protect_request`, agora exige `localhost`, `127.0.0.1` ou `::1`, reduzindo a superfície de DNS rebinding contra o serviço local. Os testes rejeitam um domínio externo e aceitam os endereços locais.
2. **Origem de operações — defesa adicional.** POST com `Origin` diferente da origem da aplicação ou `Sec-Fetch-Site: cross-site` é rejeitado mesmo com token CSRF válido. Requisições sem esses cabeçalhos continuam exigindo CSRF. A proteção não confia em cabeçalhos encaminhados por proxy.
3. **Política do navegador — defesa adicional.** `security_headers` em `app.py:98` restringe scripts, conexões, fontes e imagens à aplicação local; bloqueia objetos, enquadramento e mudança de URL base. Câmera, microfone e geolocalização são desabilitados. Estilos inline continuam permitidos por compatibilidade com a interface existente; scripts inline permanecem bloqueados.
4. **Tentativas do incidente — risco médio mitigado.** O espaço de respostas objetivas do cenário é pequeno. `app.py:359` limita a 12 respostas incorretas por usuário/cenário em uma janela de 24 horas, consultando o banco dentro da transação. Limpar cookies ou reiniciar o laboratório não apaga esse histórico. Não constitui antifraude contra múltiplas contas ou colaboração externa.

O orquestrador continua executando Docker por lista de argumentos, sem shell; valida nomes/imagens e mantém publicação de portas somente em loopback, limites de recursos, capacidades removidas, sistema de arquivos somente leitura e ausência de socket Docker no container (`orchestrator.py`, funções `start` e `_docker`).

## Cópia de segurança e ensaio de restauração

A ferramenta `scripts/backup_database.py` usa a API de backup do SQLite para incluir alterações commitadas em WAL. A origem abre em modo somente leitura; o destino deve ser um arquivo novo em diretório já existente. Há verificação de integridade e limite de espera de 30 segundos. A restauração também cria um arquivo novo; não troca o banco que a aplicação está usando.

Exemplo no PowerShell, com caminhos de destino escolhidos pelo operador:

```powershell
.\.venv\Scripts\python.exe scripts/backup_database.py backup lab.db D:/backups-protegidos/purple-talent-2026-11-11.db
.\.venv\Scripts\python.exe scripts/backup_database.py restore D:/backups-protegidos/purple-talent-2026-11-11.db D:/backups-protegidos/restauracao-validada.db
```

O diretório do exemplo deve existir e ter acesso restrito. Uma cópia contém dados pessoais e hashes de senha: não publicar no GitHub nem compartilhar como evidência de QA. A ferramenta não criptografa arquivos. Para substituir o banco ativo é necessário um procedimento operacional separado, com aplicação parada e validação da restauração. Nenhum banco real foi copiado ou substituído nesta revisão.

## Verificação executada

- `python -m unittest discover -s tests -p test_security_final.py`: 4 testes aprovados (host, origem/CSRF, políticas e limite persistente).
- `python -m unittest discover -s tests -p test_backup_database.py`: 5 testes aprovados (cópia e restauração, destino existente, mesma origem/destino, fonte inválida/ausente e dados WAL).
- `git diff --check`: aprovado.

Os testes usaram arquivos sintéticos em diretório temporário no D:. Testes de navegador, suíte geral e Docker real devem ser conferidos no registro integrado da entrega.

## Limitações antes de uso público

- A conta demonstrativa do banco inicial é destinada à apresentação; provisionamento de administradores e política de credenciais precisam ser definidos para operação real (`app.py:168`). Credenciais existentes foram preservadas.
- O limitador geral está em memória por processo (`app.py:30`), portanto múltiplos processos exigem coordenação e configuração confiável de proxy.
- Sessões assinadas não oferecem revogação imediata de uma cópia de cookie. Recuperação de conta, confirmação de e-mail e autenticação adicional ainda precisam de serviço e política reais.
- O servidor Flask é local e de desenvolvimento (`app.py:638`). HTTPS, serviço de produção, isolamento operacional, monitoramento e resposta a incidentes precisam de implantação própria.
- A investigação reproduz dados fictícios para avaliação demonstrativa; seleção supervisionada exige critérios e revisão humana, e não apenas acertar um IP.
- Na revisão de dependências o coordenador identificou o aviso `GHSA-68rp-wp8r-4726` na versão Flask 3.0.3 e está integrando a versão corrigida. A versão instalada e o resultado da nova consulta devem constar da entrega integrada; `Cache-Control: no-store` já é aplicado às páginas privadas.
