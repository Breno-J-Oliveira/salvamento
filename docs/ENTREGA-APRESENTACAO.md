# Entrega para apresentação do Purple Talent

Revisão concluída em 12 de novembro de 2026 para demonstrar o recrutamento de candidatos de cibersegurança em aplicação local. Esta é a referência atual; documentos anteriores preservam os resultados de suas respectivas etapas.

## Comportamento entregue

- Landing com proposta, jornada, explicação dos dois públicos, FAQ e ilustração local original, preservando a identidade visual.
- Editor por vaga com texto curto/longo, escolha única por bolinhas e gabarito opcional, caixas de múltipla escolha, número e URL. Respostas e gabaritos versionados são relacionais. O gabarito fica na área da equipe e não decide contratação.
- Candidatura com rascunho, revisão vinculada ao conteúdo exibido, confirmação idempotente e desistência rastreável. Edições concorrentes de perguntas e pareceres geram aviso sem substituir dados silenciosamente.
- Dossiês SOC/AppSec com registros e hipóteses concorrentes. Avaliações iniciadas mantêm seu conteúdo. A equipe revisa evidências e competências e compartilha apenas o feedback apropriado.
- Console final sintético com acessos, eventos, processos, mudanças e conexões. Foram incluídas atividades legítimas e sondagens sem sucesso. As dicas foram removidas da interface dos desafios. O catálogo público continua separado da avaliação seletiva.
- Hosts locais, validação de origem de POST, CSRF, CSP, autorização e limite persistente de erros no console final. Backup/restauração para novos arquivos com integridade verificada.

## Verificação desta versão

- Chrome instalado, telas de 390 e 1440 px: landing com imagem carregada, FAQ funcional e sem transbordamento. Revisão visual móvel realizada.
- 15 cenários de recrutamento e 10 cenários de gestão de vagas aprovados no navegador em banco sintético separado.
- Suíte integrada final em Flask 3.1.3: 147 testes distribuídos em três processos isolados (51, 64 e 32); 146 aprovados e 1 teste Docker opcional ignorado nessa execução. Nenhuma falha.
- O teste Docker opcional foi então executado: 17/17 casos do orquestrador aprovados, incluindo o teste real previamente ignorado. O novo teste real do console também passou, cobrindo duas instâncias, sete rotas por instância, portas/dados distintos, ausência da semente nas respostas e encerramento independente. Assim, os 148 casos Python únicos atualmente descobertos foram verificados, incluindo os casos Docker.
- As duas imagens foram reconstruídas com Flask 3.1.3. Compilação Python, `pip check` e `git diff --check` aprovados. Servidor principal reiniciado; landing HTTP 200 e cabeçalho CSP confirmados.
- Comandos: `python -m unittest discover -s tests -v` (a execução final dividiu as suítes por módulo em três processos), `RUN_DOCKER_TESTS=1` para test_orchestrator.py e test_incident_docker.py, testes/browser_recruitment.cjs e browser_vacancies.cjs no Chrome instalado. Logs finais sintéticos: final-0.log, final-1.log, final-2.log, browser-final.log, vacancies-final.log, orchestrator-final.log e incident-docker-final.log em D:/purple-talent-qa.
- Dependências instaladas consultadas em OSV: Flask 3.1.3, Werkzeug 3.1.9, Jinja2 3.1.6, itsdangerous 2.2.0, click 8.5.0, blinker 1.9.0 e MarkupSafe 3.0.4, sem avisos retornados nessa consulta. O Flask 3.0.3 foi atualizado após detecção de [GHSA-68rp-wp8r-4726](https://github.com/advisories/GHSA-68rp-wp8r-4726). A ausência de avisos não comprova ausência de vulnerabilidades.
- Evidências sintéticas ficam em D:/purple-talent-qa e output/qa, fora da publicação. Não são utilizados dados pessoais do banco da equipe nos testes.

## Escopo e limites

A entrega é local e apropriada para demonstração supervisionada. Não representa homologação de uso público, aceite da empresa ou comprovação antifraude. Os laboratórios exibem capturas fictícias; não há ataque real em andamento. Os testes não cobrem todas as possibilidades e não substituem uso com pessoas, leitor de tela ou auditoria independente.

Antes de implantação empresarial pública: provisionar equipe sem credenciais demonstrativas, definir HTTPS/hospedagem, política de dados e retenção, recuperação de acesso, separação de papéis, operação de backup, revogação de sessões e limitação coordenada entre processos. Os detalhes estão em SEGURANCA-FINAL.md. A lista de 30 melhorias é um backlog; itens não verificados não são apresentados como concluídos.

Roteiro e comandos operacionais: APRESENTACAO.md. Contexto de continuidade: claude.md.
