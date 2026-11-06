# Purple Talent — contexto e continuidade do projeto

Consolidação em 6 de novembro de 2026. Este arquivo resume o contexto de trabalho da conversa, as decisões do usuário e as evidências disponíveis. É uma passagem de contexto para continuidade, não uma transcrição literal de todas as mensagens. Não contém segredos, banco de usuários ou instruções internas das ferramentas.

## Pedido de salvamento

O usuário pediu criar `claude.md` com o contexto do chat e salvar a versão local completa em `Breno-J-Oliveira/salvamento`. Esse salvamento inclui as melhorias locais ainda não publicadas em `purple-talent`. A autorização de salvamento não autoriza publicar essas melhorias em `purple-talent`.

## Projeto e propósito

Purple Talent é a proposta de plataforma do projeto SAGA / Projeto Integrador SENAI / Desafio de Ideias. O objetivo é transformar desempenho prático de estudantes em desafios Capture a Bandeira em evidências úteis ao recrutamento de estágio e vagas júnior de cibersegurança. LabWare é o contexto de empresa apresentado pelo usuário; não afirmar parceria formal, aceite institucional ou uso em produção sem comprovação.

A pergunta central é: um CTF Purple Team pode ajudar empresas a identificar e selecionar talentos de segurança? A proposta reúne prática ofensiva e defensiva, avaliação humana e apresentação das evidências. Currículos são complementados por resultados observados; pontuação não equivale a garantia de competência ou contratação automática.

Áreas conceituais: Arenas e desafios CTF; Talent Pool e ranking; dossiê do candidato; vagas e matchmaking. A dinâmica original envolve equipes Red e Blue, troca de papéis, proteção e captura de uma bandeira e relatório final das vulnerabilidades e mitigações.

## Personas e descoberta fornecidas

- Camila Rocha, 34 anos, Tech Recruiter sênior no cenário LabWare: precisa avaliar prática, reduzir triagem de currículos e atrair talentos universitários. É a principal persona de recrutamento.
- Mateus Santos, 21 anos, estudante de Segurança da Informação e suporte técnico: busca primeiro estágio/júnior e oportunidade de demonstrar prática.
- Marina Silva, 33 anos, coordenadora AppSec: integração entre equipes, segurança aplicada e resposta rápida.
- Beatriz Bia Lima, 21 anos, profissional júnior/estagiária: experiência prática e confiança para lidar com incidentes.

A matriz CSD distingue certezas, hipóteses e dúvidas. Redução de mais de 50% do tempo de triagem, aprovação de orçamento e preferência por seleção gamificada eram hipóteses, não resultados medidos. Critérios de avaliação, confiança no ranking, formato do relatório e capacidade do laboratório ainda exigem validação humana.

Prioridades originalmente indicadas: pontuação, ranking, relatório e evidências de ataque/defesa. Certificados, gamificação adicional e personalização avançada eram secundários. O foco deve continuar sendo converter prática em informação compreensível para a mentoria e recrutamento.

## Histórico de decisões

1. A concepção inicial previa PHP/HTML, JavaScript, Tailwind/CSS, Node/Fastify, Prisma/PostgreSQL e Docker Compose. Houve planejamento e implementação inicial nessa stack.
2. O usuário pediu autonomia, subagentes, qualidade profissional, atenção à usabilidade e publicação por marcos. Pediu README inspirado no NexusAuth.
3. Posteriormente mandou interromper a abordagem anterior: sua equipe entregou outra base e a Scrum Master orientou integrar Docker e o frontend da Rafaela, evitando adicionar tecnologias e complicar o projeto.
4. A base encontrada na pasta já tinha sido substituída pela equipe por Flask, SQLite, HTML/Jinja, CSS, JavaScript e Docker. Essa é a arquitetura atual. Não restaurar automaticamente PHP/Node/PostgreSQL a partir do planejamento antigo.
5. Foram integradas telas funcionais, segurança, testes, Docker e documentação. O usuário inicialmente proibiu publicação.
6. Depois forneceu `Purple Talent.zip`, com oito PNGs Desktop, e referências `style.css`, `app.js` e `index (6).html`. Pediu priorizar o modelo visual do Figma.
7. O frontend de referência era um protótipo com localStorage. O visual foi adaptado mantendo contas, sessões, pontuação e regras no servidor.
8. O usuário autorizou substituir o conteúdo de `purple-talent` pela versão local. A atualização foi publicada preservando histórico, sem force push. Alterações remotas diferentes da versão local foram conscientemente substituídas conforme essa autorização.
9. Pediu ampliar o projeto, adicionar desafios, corrigir CSS da Intranet esquecida e sugerir pelo menos cinco melhorias. Depois restringiu a publicação: somente a correção CSS poderia ir a `purple-talent`; todas as demais evoluções deveriam ficar locais.
10. O pedido atual autoriza salvar o conjunto local em outro repositório, `salvamento`.

## Identidade visual e referências

Primeira referência preservada: `stitch_purple_ctf_talent_platform`, com HTML, imagens e DESIGN.md. A nova referência Figma é prioritária: fundo roxo quase preto, painéis roxos escuros, botões violeta, navegação horizontal, cabeçalhos grandes, autenticação em duas colunas e lista horizontal de desafios.

Paleta atual aproximada: fundo #0e0c17, painéis #161326, bordas #2d2748, texto #ece8fa, primária #a855f7 e tons auxiliares azul/vermelho. Fontes locais: Plus Jakarta Sans, Inter e JetBrains Mono, com licenças. O código de referência citava Sora/IBM Plex Mono por CDN; a aplicação conserva as fontes locais.

Preservar a identidade em futuras mudanças. Evitar trocar o layout inteiro por iniciativa própria. Animações sutis respeitam prefers-reduced-motion; impressão não deve herdar animações ou controles interativos.

Referências de entrada estavam em arquivos locais do usuário e não são pré-requisito para executar a aplicação. O ZIP continha imagens, não código. Não copiar textos como ao vivo, VMs prontas, convites automáticos ou dados só neste navegador se isso não representar o funcionamento real.

## Arquitetura atual

- Python 3.12 e Flask 3.0.3 processam rotas, autenticação, autorização e regras.
- SQLite persiste contas, desafios, tentativas, instâncias, avaliações, oportunidades, candidaturas e relatos.
- HTML/Jinja, CSS e JavaScript locais compõem a interface. Não há React nem API Node nesta versão.
- Docker CLI no host cria os laboratórios. Compose prepara imagem e laboratório manual de diagnóstico.
- catalog.py contém oito desafios incrementais novos.
- learning.py registra progresso e relatos e suas estruturas de banco.
- Somente ferramentas de QA/documentação usaram Playwright e python-docx; essas ferramentas não são dependências do produto.

O servidor é local, vinculado a 127.0.0.1, sem debug. Não foi homologado como serviço de produção. Não montar socket Docker em um serviço web para simplificar a execução.

## Funcionalidades implementadas

- Cadastro de participante, login, logout por POST e edição de nome/equipe.
- Cadastro nunca concede mentor pelo campo enviado pelo cliente. Papéis são revalidados no banco.
- Início público com métricas reais; navegação para desafios, Purple Team, laboratório, blog, ranking e empresas.
- Busca de desafios por texto e filtro por área; briefing, dicas e validação de flags.
- Intranet Docker individual, com flag aleatória, porta local e expiração.
- Ranking e métricas por equipe; notas humanas de lógica, comunicação, colaboração e decisão, entre 1 e 5.
- Dossiê do candidato com tentativas, avaliações e impressão.
- Mentoria cadastra, pausa e reabre vagas; participante registra candidatura única. Mentoria consulta candidatos da vaga.
- Compatibilidade de vaga é proporção entre pontuação total e mínima, limitada a 100%; seleção é humana.
- Blog possui guias expansíveis reais sobre codificação, logs, robots.txt e Docker.
- Purple Team apresenta o percurso de ataque, defesa e aprendizagem, sem simular recursos inexistentes.
- Catálogo local ampliado de 4 para 12 desafios.
- Painel Minha evolução com progresso por categoria e últimas 20 tentativas.
- Participante que concluiu desafio pode salvar/atualizar relato de 30 a 6000 caracteres. A mentoria consulta os relatos no dossiê.

Os quatro desafios originais são Boas-vindas, Intranet esquecida, Texto estranho e Quem está atacando. Os oito novos tratam de César, Base64 duplo, ASCII, cabeçalhos HTTP, correlação de autenticação, assinatura de arquivo, permissões e contenção de incidente. O seed é incremental e idempotente por título, não altera respostas/submissões existentes e preserva os IDs originais.

## Segurança e regras

Sessão com chave persistente local ou variável SECRET_KEY, cookie HttpOnly/SameSite, CSRF em todos os POST, validações de comprimento e conteúdo, queries parametrizadas, escape Jinja, cabeçalhos de proteção, limite de corpo e limitação de tentativas por identidade/rota.

Flags erradas não pontuam. Um desafio pontua uma vez por conta; transação revalida conclusão em concorrência. Flag de laboratório precisa pertencer a instância própria, ativa e não expirada. Relatos exigem conclusão na própria conta. Avaliações e gestão de vagas/ambientes requerem mentor.

Nunca registrar senhas, cookies, flags reais ou dados pessoais em logs de teste. Não versionar .env, .session-key, lab.db, volumes, .venv, node_modules, logs ou output privado. O banco existente e as credenciais da equipe foram preservados. O seed tem acesso demonstrativo documentado no README, exclusivo para uso local.

## Docker e seus limites

Imagem permitida: cti-lab/web-01. Container executa usuário 10001, filesystem somente leitura, capabilities removidas, no-new-privileges, 128 MiB, 0,5 CPU, 64 processos e /tmp limitado a 16 MiB. Porta atribuída pelo Docker vinculada a 127.0.0.1. A flag vai pelo ambiente, sem valor no argv. Há healthcheck e espera HTTP para readiness.

Bridge dedicada com ICC=false reduz comunicação direta entre instâncias. Não é isolamento absoluto do host/saída nem sandbox de execução arbitrária. Não existem VMs Kali/Windows completas nesta versão.

Limites funcionais: 10 instâncias globais, 2 por participante, duração de 60 minutos. O processo web executa limpeza periódica; se fechado, a remoção física depende de sua próxima execução. Locks e rate limiting em memória não coordenam múltiplos processos.

Erros do Docker não são silenciados nem expõem stderr bruto. Falha de parada preserva registro ativo. Instância ausente é reconciliada sem limpeza global ou remoção de recursos alheios. O Docker tem apresentado inicialização e operações lentas neste PC; o teste de navegador usa prazo compatível com as chamadas da CLI.

## Correção CSS publicada separadamente

A Intranet esquecida tinha texto de ajuda invadindo o botão Iniciar ambiente por herdar margin-top negativo de field-help. A correção isolada adicionou challenge-layout, espaçamento positivo, grid minmax(0,...), quebra de logs/URLs longos e tratamento de mobile/impressão.

Somente `templates/challenge.html` e `static/pages.css` foram enviados nesse marco. Publicação confirmada: commit 1953f0a1df302fb81f18bf8009c03819f3f6ab26 em purple-talent. Não enviar as evoluções locais a esse repositório sem nova autorização.

## Escalabilidade já trabalhada e limites

O ranking foi refeito com agregações SQL/CTEs em vez de consultas por participante. Índices incrementais atendem consultas de tentativas, instâncias, avaliações e candidaturas. Novos módulos isolam catálogo e aprendizagem sem adicionar infraestrutura.

Ainda não há paginação completa, fila persistente de provisionamento, controle multiprocesso, auditoria externa, backup/restauração homologados ou teste de carga prolongado. SQLite/servidor local e Docker bridge não devem ser vendidos como arquitetura pronta para serviço público de grande escala.

## Verificação observada

- Marco Figma anterior: 45 testes Python e 14 cenários Chrome aprovados, com Docker real.
- Evolução local atual: 53 testes Python executados, 52 aprovados e 1 teste Docker opcional ignorado nessa suíte.
- Bateria separada atual: 15 cenários Chrome aprovados, incluindo cadastro, login, filtros, flags, perfil, permissões, avaliação, impressão, vagas, novas páginas, progresso/relato e ciclo real Docker de início, solução e encerramento.
- CSS Intranet: Chrome 375/768/1440 px, ausência de sobreposição/overflow, texto longo e impressão verificados.
- Sintaxe Python e git diff --check aprovados na etapa anterior.

Os resultados são evidências de execuções anteriores, não garantia permanente. Reexecutar verificações proporcionais depois de alterações. Testes com mocks não comprovam Docker real; testes automáticos não substituem aceite humano. Expiração foi exercitada com registros/condições controladas, sem esperar uma hora real.

Evidências locais ficam em output/qa, ignoradas pelo Git. Não estão incluídas neste salvamento por conterem dados e sessões de QA.

## Execução e testes

No Windows PowerShell, na raiz:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
docker compose --profile manual build web01
.\.venv\Scripts\python.exe app.py
```

Aplicação em http://127.0.0.1:5000. Abrir Docker Desktop e aguardar engine Linux ativo. Banco é criado/preservado localmente. Não apagar banco ou volumes para resolver inicialização.

```powershell
.\.venv\Scripts\python.exe tests/run_report.py
$env:RUN_DOCKER_TESTS='1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_orchestrator.py -v
Remove-Item Env:RUN_DOCKER_TESTS
```

Para testes de navegador, iniciar tests/serve_browser.py na porta 5055 e executar tests/browser.cjs com Playwright disponível no ambiente de QA. Não é preciso adicioná-lo às dependências do produto. Usar npm.cmd se npm.ps1 sofrer bloqueio no PowerShell.

## Documentação

README.md: execução e arquitetura. docs/DOCKER.md: diagnóstico e restrições. docs/mudanca.md: mudanças por etapa. docs/PROXIMAS-MELHORIAS.md: propostas futuras. docs/Plano de Testes de Software & GOT.docx: relatório histórico baseado em modelo de checkout fornecido pelo usuário, adaptado ao Purple Talent. docs/casos-got.json e docs/build_test_report.py: fonte e gerador.

O Word foi conferido estruturalmente, mas sua renderização/paginação não foi validada porque o runtime da época não tinha Word/LibreOffice disponíveis. O DOCX é histórico e não foi regenerado a cada evolução; consultar os registros de execução e mudanca.md para resultados posteriores. O gerador ainda depende do documento modelo em caminho local do autor; adaptar esse recurso antes de exigir geração em outra máquina.

## Próximas melhorias propostas, ainda não implementadas

1. Rodadas Purple Team com relatório, rubrica e feedback humano.
2. Eventos/turmas com participantes, desafios e rankings separados.
3. Busca de talentos por evidências, distinguindo habilidades declaradas de observadas.
4. Trilhas com pré-requisitos e recomendações explicáveis.
5. Gestão editorial de desafios com versões e validação antes da publicação.
6. Provisionamento assíncrono persistente, quotas atômicas e reconciliação independente do servidor web.
7. Backup/restauração testados, monitoramento e auditoria com retenção definida.
8. Consentimento granular de visibilidade do perfil, contato mediado e exportação de dados.

## Orientações para continuar

Responder em português brasileiro. Preservar stack, visual Figma, dados e alterações da equipe. Não afirmar aprovação da Scrum Master ou da LabWare sem evidência. Não introduzir tecnologias só para sofisticar o projeto. Delegar apenas frentes independentes, com ownership de arquivos; não permitir edições concorrentes no mesmo arquivo.

Trabalhar com mudanças incrementais, validação real e distinção entre planejado, implementado e verificado. Solicitar autorização específica para produção, custos, credenciais, exclusões amplas ou alterações destrutivas. Publicação de recursos novos em purple-talent continua restrita; o salvamento autorizado aqui é em salvamento.

O usuário quer um projeto profissional para portfólio e uso sério pela equipe. A revisão e o aceite humanos continuam necessários. Não prometer funcionamento perfeito em todos os ambientes ou cobertura de todas as possibilidades.

