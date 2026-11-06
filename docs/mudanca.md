# Mudanças da integração Purple Talent

Data de consolidação: **5 de novembro de 2026**.

## Escopo recebido e base preservada

Esta entrega integra a versão disponibilizada pela equipe à interface de referência da pasta `stitch_purple_ctf_talent_platform` e aos laboratórios Docker. A orientação mais recente substituiu o planejamento anterior: trabalhar sobre o que a equipe entregou, evitar novas tecnologias e não publicar no GitHub.

A base encontrada já era **Python, Flask 3.0.3, SQLite, HTML/Jinja, CSS, JavaScript e Docker**. As pastas da implementação antiga PHP/Node/PostgreSQL já estavam ausentes quando esta etapa começou. Elas não foram restauradas. As exclusões que aparecem no Git em relação ao histórico anterior não representam uma remoção feita durante esta integração.

O banco `lab.db` da equipe foi preservado. Os testes usaram bancos temporários ou `output/qa/browser.db`. As referências visuais originais não foram alteradas. Nenhum commit ou envio ao GitHub foi realizado nesta etapa.

## Interface integrada

Foram integrados doze templates, usando a base de componentes compartilhada em `templates/base.html`:

| Tela | Comportamento implementado |
| --- | --- |
| Login | Autenticação por e-mail e senha, mensagens de falha e navegação para cadastro |
| Cadastro | Conta de participante com nome, e-mail, senha e equipe opcional |
| Arenas | Desafios persistidos, pontos, estado de conclusão, busca por texto e filtro por área |
| Desafio | Briefing, dica, envio de flag, resultado e controle da instância individual |
| Ranking | Classificação por pontos reais, desempate por ID e busca |
| Perfil | Edição do próprio nome/equipe e consulta ao progresso |
| Painel de mentoria | Desempenho individual e por equipe, com acesso aos dossiês |
| Dossiê | Histórico de tentativas, avaliações, notas de quatro competências e impressão |
| Ambientes | Consulta e encerramento de instâncias pela mentoria |
| Vagas | Criação, pausa, reabertura, indicador de pontuação e candidatura |
| Estados de erro | Mensagens para 400, 403, 404, 405, 413 e 429, com recuperação por navegação |
| Layout compartilhado | Menu por papel, perfil, saída, foco visível, link de salto e rodapé |

Foram mantidos o fundo `#0f131c`, os painéis `#181b25`, o roxo `#ddb7ff` e os canais azul/vermelho da identidade Purple Team. As fontes **Plus Jakarta Sans, Inter e JetBrains Mono** são servidas localmente, com suas licenças. Não há dependência de CDN de fontes, CSS ou JavaScript.

O layout adapta menu, cartões, formulários e tabelas para celular e tablet. Tabelas podem ter rolagem dentro do próprio contêiner, sem alargar a página. Foram adicionados estados vazios, feedback das operações, confirmação de encerramento coletivo, estado de preparação do laboratório e indicação de expiração. O favicon acompanha a marca da interface.

Métricas demonstrativas do protótipo foram substituídas pelos dados disponíveis na aplicação. Não são anunciados VPN, Kubernetes, detecção automática de fraude, contratação automática ou infraestrutura que esta versão não possui.

## Lógicas e persistência

### Cadastro e sessão

- E-mail normalizado, nome e equipe limitados, senha entre 8 e 128 caracteres.
- Senhas persistidas por hash; cadastro público sempre cria participante, mesmo se o cliente enviar `role=mentor`.
- Chave de sessão aleatória e persistente em `.session-key`, com alternativa de variável `SECRET_KEY`.
- Cookie HttpOnly e SameSite Lax; sessão com duração limitada; logout por POST.
- Papel e existência do usuário consultados no banco em cada requisição autenticada.
- Credenciais existentes preservadas; o acesso de demonstração herdado da equipe permanece restrito ao uso local.

### Desafios e pontuação

- Quatro desafios da base continuam disponíveis: boas-vindas, intranet, codificação Base64 e investigação de logs.
- Tentativas incorretas não pontuam. Flags vazias ou extensas são rejeitadas.
- Cada desafio pontua uma vez por participante. A transação SQLite revalida a conclusão para evitar duplicação por requisições concorrentes.
- POST em desafio já concluído redireciona, evitando reapresentar um formulário como resultado de uma submissão repetida.
- Flag de laboratório é validada somente contra instância própria, ativa e dentro do prazo.
- Ranking e painel usam conclusões únicas, tentativas, tempo médio e avaliações registradas.

### Avaliação e oportunidades

- Mentores registram raciocínio lógico, comunicação, colaboração e decisão, com notas inteiras de 1 a 5.
- Entradas inválidas não são silenciosamente arredondadas ou ajustadas.
- Dossiê reúne histórico e observações, com apresentação de impressão.
- Tabelas `jobs` e `applications` foram adicionadas de forma incremental.
- Mentor cria, pausa e reabre vagas; participante pode candidatar-se uma única vez por vaga.
- Vagas pausadas recusam novas candidaturas. Mentores visualizam as pessoas inscritas e acessam seus dossiês.
- Compatibilidade compara pontuação total e pontuação mínima, limitada a 100%. A seleção continua sendo humana.

## Integração Docker

A aplicação Flask roda no host e usa a CLI Docker para criar os laboratórios. O Compose prepara a imagem e oferece um perfil manual de diagnóstico. Não foi montado o socket Docker dentro da aplicação ou dos desafios.

| Controle | Configuração |
| --- | --- |
| Imagem permitida | `cti-lab/web-01` |
| Porta do laboratório | 5000 dentro do container, porta externa dinâmica |
| Exposição | Apenas `127.0.0.1` |
| Identidade | Usuário `10001:10001` |
| Filesystem | Somente leitura; `/tmp` temporário limitado a 16 MiB |
| Recursos | 128 MiB, 0,5 CPU e 64 processos |
| Privilégios | Todas as capabilities removidas e no-new-privileges |
| Rede | Bridge dedicada, comunicação direta entre containers desabilitada por ICC |
| Disponibilidade | Endpoint `/health`, healthcheck da imagem e espera HTTP antes de retornar a porta |
| Instância | Flag aleatória por participante, nome validado e etiqueta do projeto |
| Limites funcionais | 10 instâncias globais, 2 por participante, prazo de 60 minutos |

O Docker escolhe a porta de forma atômica. A flag é passada via ambiente do processo, sem aparecer nos argumentos da CLI. Erros internos do Docker não são exibidos integralmente ao usuário.

O encerramento de container ausente é idempotente. Uma falha real do daemon é propagada à aplicação, que mantém o registro ativo em vez de afirmar que a operação terminou. Containers de outros projetos são recusados pelo nome e pela etiqueta.

A inicialização não desativa mais todas as instâncias do banco nem executa uma limpeza global. A tela de desafio e a tentativa de reinício reconciliam a ausência de um container. Se o estado do Docker não puder ser confirmado, a tela informa a indisponibilidade e preserva o registro, sem oferecer um link como se o laboratório estivesse confirmado.

O processo da aplicação faz a limpeza periódica dos expirados. Se estiver fechado, o prazo continua impedindo a validação da flag, mas a remoção física depende de o processo voltar a executar. Instruções e diagnóstico estão em `docs/DOCKER.md`.

## Segurança e correções

| Problema observado | Correção |
| --- | --- |
| Formulários sem proteção CSRF | Token vinculado à sessão em todos os POST |
| Token Unicode causando exceção | Comparação constante em bytes UTF-8 e rejeição HTTP 400 |
| Cadastro e avaliação sem validação completa | Limites e mensagens explícitos no servidor |
| Permissão mantida apenas na sessão | Papel revalidado no banco |
| Reenvio e concorrência | Transação de pontuação e unicidade de candidatura |
| Inicialização apagando estado operacional | Registros preservados e reconciliação direcionada |
| Erros de encerramento ignorados | Estado só atualizado após confirmação |
| Escolha prévia de porta livre | Alocação pelo Docker |
| Vazamento de detalhes em erro Docker | Mensagem pública genérica, sem stdout/stderr bruto |
| Banco e chave expostos ao versionamento | Regras `.gitignore` para dados, segredos e evidências |
| Excesso de tentativas e payload | Limitação por identidade/rota e corpo de até 64 KiB |
| XSS e SQL injection | Escape padrão Jinja e consultas parametrizadas; testes adversariais |
| Configuração de execução inadequada | Debug desligado e bind local do Flask |

Cabeçalhos `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` e controle de cache foram incluídos. A configuração não é uma certificação de segurança nem substitui avaliação para produção.

## Verificação executada

**Resultado consolidado: 58 cenários aprovados**, sendo **45 testes automatizados Python** e **13 cenários de navegador Chrome**. O teste Python de Docker real foi habilitado e passou; não foi contado como sucesso enquanto estava ignorado.

Comandos e evidências:

- Instalação das dependências existentes em `.venv` concluída.
- `python tests/run_report.py` com `RUN_DOCKER_TESTS=1`: 45 testes, zero falhas, zero ignorados.
- `docker --context desktop-linux compose --profile manual build web01`: build aprovado.
- `docker --context desktop-linux compose --profile manual config --quiet`: configuração aprovada.
- `node --check static/app.js`: sintaxe aprovada.
- `node tests/browser.cjs` com `RUN_DOCKER_TESTS=1`: 13 cenários aprovados.
- Teste direcionado de indisponibilidade Docker reexecutado após o ajuste do estado visual: aprovado.
- Instância local da porta 5000 reiniciada para carregar as correções; login respondeu 200 e token Unicode adulterado respondeu 400 na instância final.
- Capturas reais em 375, 768 e 1440 px, com conferência de ausência de overflow da página.
- Inspeção visual das arenas e das telas de mentoria em desktop/mobile.
- Jornada real: iniciar intranet pela tela, consultar `robots.txt`, descobrir flag, submeter, concluir e encerrar.
- Dois containers simultâneos: flags e portas distintas, parâmetros de segurança verificados e encerramento independente.

Os testes adversariais cobrem SQL injection em login, XSS no nome, adulteração de papel, acesso de participante às funções de mentor, instância de outro usuário, token ausente/incorreto/Unicode, excesso de corpo, limite de tentativas, dados inválidos, dupla candidatura e submissões simultâneas.

A primeira execução do cenário concorrente identificou resposta 200 em uma repetição já resolvida. O fluxo foi ajustado para retornar redirecionamento consistente, mantendo uma única conclusão. Também foram corrigidos dois problemas do roteiro de teste: seletor do link de avaliação e fechamento de conexões SQLite no Windows.

Os resultados individuais estão em `output/qa/unit-results.json` e `output/qa/browser-results.json`. As capturas e a impressão de dossiê também ficam nessa pasta, ignorada pelo Git. Playwright e python-docx foram usados somente como ferramentas de QA/documentação; não foram adicionados às dependências da aplicação.

O servidor de QA da porta 5055 foi encerrado após os testes. Os containers criados pelos testes foram encerrados. A aplicação atual ficou disponível em `http://127.0.0.1:5000`, usando o banco da equipe e mantendo os logs locais em `.runtime`, fora do versionamento.

## Documentos e arquivos

- `README.md`: execução atual e limites do ambiente local.
- `docs/DOCKER.md`: preparação, diagnóstico, isolamento e testes Docker.
- `mudanca.md`: este registro.
- `Plano de Testes de Software & GOT.docx`: identificação, estratégia, regras, matriz dos 58 cenários, correções, comandos, resultados e rastreabilidade.
- `docs/casos-got.json` e `docs/build_test_report.py`: fonte rastreável e gerador do relatório.
- `tests/test_app.py`, `tests/test_edge_cases.py`, `tests/test_lab.py` e `tests/test_orchestrator.py`: testes automatizados.
- `tests/run_report.py`, `tests/serve_browser.py` e `tests/browser.cjs`: execução e evidências isoladas.

## Limites e aceite humano

Esta entrega foi verificada para demonstração e uso **local**. Não houve deploy em produção, teste de carga prolongado, auditoria externa, certificação de acessibilidade, validação multiusuário remoto ou teste de recuperação após falha elétrica. A expiração foi testada por condições controladas, sem aguardar sessenta minutos reais.

A rede e as restrições dos containers reduzem exposição, mas não constituem isolamento absoluto nem um executor seguro de código arbitrário. Os laboratórios não devem ser expostos à internet.

O documento Word foi gerado e sua estrutura/conteúdo foram conferidos. A renderização e revisão final de paginação ficaram pendentes porque o runtime documental Windows não fornece LibreOffice e não há Word disponível. Essa limitação documental não foi apresentada como teste aprovado.

O aceite final cabe à equipe e à Scrum Master, avaliando as telas, os critérios do desafio e as regras simplificadas de vagas. Nenhuma aprovação humana ou institucional foi presumida.

## Refinamento visual e organização dos documentos

Em 5 de novembro de 2026, foram acrescentadas transições discretas para botões, campos, navegação e cards, uma entrada breve da área de conteúdo, abertura suave dos painéis e um indicador de carregamento durante a preparação do laboratório. Layout, textos, fontes, paleta e regras de negócio foram preservados; nenhuma dependência foi adicionada.

Os efeitos respeitam `prefers-reduced-motion` e não são aplicados à impressão. Os documentos foram reunidos em `docs/mudanca.md` e `docs/Plano de Testes de Software & GOT.docx`. O Word foi movido sem alteração de conteúdo, com hash SHA-256 conferido antes e depois. README e destino do gerador foram atualizados.
Verificação deste refinamento: navegador Chrome em desktop e celular, abertura de painel, preferência por movimento reduzido, impressão sem animação e ausência de exceções JavaScript aprovados. Sintaxe JavaScript e git diff --check aprovados.

## Integração do novo frontend de 6 de novembro de 2026

Referências recebidas: oito imagens de Purple Talent.zip e arquivos HTML/CSS/JavaScript da equipe. O novo visual prioriza as imagens: navegação horizontal, painéis roxos escuros, botões violeta, lista horizontal de desafios e formulários em duas colunas. Foram criadas página inicial com métricas reais, página de laboratório, blog de estudos com guias expansíveis e apresentação Purple Team. Perfil, ranking, vagas e mentoria seguem conectados ao banco.

O JavaScript de referência era um protótipo localStorage. A integração mantém autenticação, autorização, flags e pontuação no Flask/SQLite. Os números de exemplo foram substituídos pelos dados existentes. A infraestrutura disponível continua sendo o laboratório Docker; não há VMs Kali/Windows ou convites automáticos simulados como reais. A stack e os dados existentes foram preservados.
Verificação em 6 de novembro: os 14 cenários de navegador passaram, incluindo as novas páginas em desktop/mobile e o ciclo Docker real. A publicação da versão local foi autorizada pelo usuário, substituindo o conteúdo remoto e preservando o histórico. Banco local, chaves e evidências privadas permanecem ignorados.

## Evolução local após integração Figma

Apenas a correção visual da página Intranet esquecida foi autorizada e publicada (commit 1953f0a): texto de ajuda separado do botão, grid responsivo e contenção de textos longos. Verificação Chrome 375/768/1440 px e impressão aprovadas. Os demais recursos desta seção permanecem locais.

Foram acrescentados oito desafios educativos com seed incremental idempotente, preservando os quatro desafios originais e suas submissões. Novos temas: César, Base64 duplo, ASCII, cabeçalhos HTTP, correlação de autenticação, assinatura de arquivo, permissões e resposta a incidente.

O painel Minha evolução mostra progresso por área e últimas 20 tentativas. Após concluir um desafio, o participante pode salvar e atualizar um relato de 30 a 6000 caracteres. A mentoria consulta esses relatos no dossiê. O servidor verifica propriedade e conclusão e escapa o texto na apresentação.

A consulta do ranking passou de várias consultas por participante a uma agregação SQL com CTEs. Índices incrementais foram criados para tentativas, instâncias, avaliações e candidaturas. Não houve troca de stack, limpeza de dados ou dependência nova.
Validação local adicional: 15 cenários Chrome aprovados, incluindo painel de evolução, persistência do relato, responsividade e início/solução/encerramento Docker reais. A aplicação em 127.0.0.1:5000 respondeu HTTP200 com os 12 desafios após reinício. A lentidão de encerramento Docker exigiu prazo de teste compatível com o timeout da CLI.
Regressão final: 53 testes Python executados, 52 aprovados e 1 integração Docker opcional ignorada nessa suíte; o Docker real foi exercitado e aprovado na bateria separada de 15 cenários Chrome. Sintaxe Python e git diff --check aprovados. As novas melhorias continuam somente locais.
