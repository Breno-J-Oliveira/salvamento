# Purple Talent — contexto e continuidade do projeto

## Leia primeiro estado consolidado em 12 de novembro de 2026

Esta seção e as duas entregas imediatamente abaixo representam o estado atual. Se houver conflito com registros antigos deste arquivo, use esta consolidação e os relatórios vinculados; o restante é histórico.

- **Publicação confirmada antes desta atualização documental:** main de Breno-J-Oliveira/salvamento, commit f0c515d4608586182bf6837943abe7b94e68e4a6. A versão anterior de apresentação está em 9f44235e393814763ff5d0f572675537a0a52482. Os commits locais têm SHAs diferentes porque a publicação foi feita pela integração GitHub; o conteúdo enviado foi conferido por hash de cada arquivo.
- **Execução:** Windows PowerShell, .venv/Scripts/python.exe app.py, endereço http://127.0.0.1:5000. Para Docker, abrir Desktop e aguardar o engine Linux. O processo local foi reiniciado após a evolução; sua disponibilidade futura deve ser verificada, não presumida.
- **Novas rotas:** /opportunities aceita q, side e modality combinados; /my-applications aceita status; /my-applications/<id>/receipt exige participante titular e oferece extrato imprimível. O extrato não inclui gabarito nem notas internas. A lista de laboratórios também exige login e nunca expõe instâncias de outro usuário.
- **Arquivos da evolução:** recruitment.py, app.py, static/app.js, templates/admin_job_form.html, templates/opportunities.html, templates/my_applications.html, templates/application_receipt.html e templates/laboratory.html. Os estilos editor-enhancements.css, candidate-enhancements.css e workspace-enhancements.css são incluídos em templates/base.html.
- **Verificação registrada da evolução:** 18 cenários Chrome integrados, 7 testes novos da jornada e 3 dos laboratórios aprovados. QA independente conferiu 8 telas móveis/desktop e impressão, incluindo título longo e URL extensa. O editor foi verificado com duplicação, reordenação, desfazer, identificadores únicos, limite de 15 perguntas, prévia, contadores e aviso ao sair. Não alegar que a suíte integral foi reexecutada nesta evolução.
- **Verificação da apresentação anterior:** os 148 casos Python únicos foram verificados, incluindo os casos reais Docker executados separadamente, e 25 cenários de navegador passaram naquela etapa. Consulte os relatórios para distinguir datas, cobertura e resultados; não somar testes repetidos como casos novos.
- **Preservação:** não excluir lab.db, .session-key, candidaturas, snapshots ou backups; não executar testes no banco da equipe. Fixtures e evidências sintéticas ficam no D: ou em output/qa ignorado pelo Git. O disco C: voltou a ficar com pouco espaço durante a última etapa; verificar espaço antes de rebuilds ou testes extensos.
- **Próximas mudanças:** priorizar problemas comprovados e os limites empresariais registrados, sem inventar validação humana, parceria formal ou uso público. Há um backlog de 30 propostas; a lista não equivale a 30 funcionalidades concluídas. Publicação autorizada somente no salvamento; não enviar estas evoluções para purple-talent.

Referências atuais: [23 melhorias](docs/EVOLUCAO-23-MELHORIAS.md), [entrega de apresentação](docs/ENTREGA-APRESENTACAO.md), [roteiro](docs/APRESENTACAO.md), [segurança](docs/SEGURANCA-FINAL.md) e [avaliação](docs/AVALIACAO-FINAL.md).


## Evolução de usabilidade após a entrega de apresentação

Foram integradas 23 melhorias, detalhadas em docs/EVOLUCAO-23-MELHORIAS.md: editor com duplicação, reordenação, desfazer, prévia, contadores e aviso ao sair; filtros de vagas/candidaturas, datas, histórico, progresso, prazo e extrato privado imprimível; laboratórios com descrições corretas, estado individual, quota, validade, ações, conclusão e busca. Novos estilos locais são incluídos em templates/base.html. Nenhuma dependência nova foi adicionada. O extrato exige papel participante e ownership, preserva form_version e não lê notes ou answer_keys. O backend dos laboratórios não consulta Docker para construir a lista: apresenta somente registros próprios válidos e explica que a disponibilidade é confirmada no desafio.

Os 18 cenários integrados no Chrome, dez testes novos de backend e a verificação visual independente passaram. A suíte integral anterior não foi reexecutada nesta evolução; ver comandos, limites e evidências no documento específico. Publicar somente em Breno-J-Oliveira/salvamento.

## Entrega para apresentação em 12 de novembro de 2026

Esta seção prevalece sobre os estados históricos abaixo. O usuário autorizou finalizar a demonstração, melhorar segurança e UX e publicar no repositório **Breno-J-Oliveira/salvamento**. Não publicar em purple-talent. A stack permanece Flask, SQLite, HTML/Jinja, CSS/JS e Docker CLI local.

- Formulários por vaga têm texto curto/longo, escolha única com bolinhas e gabarito opcional privado, múltipla escolha, número e URL. Versões e gabaritos ficam relacionais; a nota objetiva não decide contratação.
- Candidatos revisam respostas, salvam rascunho e podem desistir nas etapas elegíveis. Há tokens de confirmação, proteção contra conflitos de respostas, perguntas e pareceres, histórico e notas internas separadas do feedback.
- A landing explica a proposta, os dois públicos, a jornada, perguntas frequentes e usa ilustração SVG local original. A identidade visual foi mantida.
- Avaliações SOC/AppSec de novas candidaturas receberam dossiês com artefatos e hipóteses concorrentes, sem resposta sugerida. Avaliações iniciadas mantêm seus snapshots. Catálogo público não é prova secreta e os botões de dicas foram removidos da interface.
- O laboratório final é captura sintética isolada em Docker, com acessos, eventos, processos, mudanças e conexões. Não é ataque real em andamento. Resposta varia por instância; há limite persistente de 12 erros/24h, independente do reinício de containers. Não é garantia antifraude.
- Segurança local: hosts permitidos, origem de POST, CSRF, CSP, permissões de navegador, cookies e autorização. Flask atualizado de 3.0.3 para 3.1.3 após consulta OSV. Não alterar credenciais ou remover banco/chave.
- scripts/backup_database.py permite backup e restauração apenas para destino novo, com verificação de integridade. Nunca usar uma base real para testes destrutivos.

Resultados e limites desta versão: docs/ENTREGA-APRESENTACAO.md. Roteiro: docs/APRESENTACAO.md. Segurança: docs/SEGURANCA-FINAL.md. Avaliação: docs/AVALIACAO-FINAL.md. Evidências com dados sintéticos ficam fora do Git. Resultados históricos não substituem a verificação final registrada nesses documentos.

A versão permanece local; uso público precisa de HTTPS/hospedagem, contas de equipe provisionadas, política de dados, recuperação de acesso, separação de papéis e validação operacional. Não prometer invulnerabilidade ou aceite empresarial.


## Continuidade local de 07/11/2026

Registro histórico da continuidade de 07/11. A consolidação no início deste arquivo prevalece.

A nova versão de salvamento (base13f9c2c) foi baixada em codex/continue-salvamento, preservando o checkout anterior em codex/before-salvamento-update. Nesta continuação foram integradas revisão humana por competência (rubric.py) e busca/filtros/paginação das candidaturas da mentoria. As notas são relacionais e internas, com justificativa, autor/data e histórico de revisões; não alteram pontos de treino, etapa ou feedback compartilhado. Apenas avaliações seletivas já enviadas podem ser revisadas. Concorrência retorna409 sem sobrescrever revisões anteriores.

GET/admin passou a filtrar candidato/vaga, etapa e vaga específica, com20 candidaturas por página. Rascunhos continuam excluídos e métricas globais são preservadas. Documentos desta etapa: docs/ENTREGA-RUBRICA.md e docs/ENTREGA-FILTROS.md. Resultados finais devem ser conferidos nesses registros; verificações anteriores não são evidência da nova etapa.

O usuário pediu testes reais Docker. As primeiras tentativas tiveram timeout/erro500 durante inicialização. Após estabilização do engine, o diagnóstico e a bateria real concluíram17/17 testes aprovados, sem alteração do código Docker ou rebuild. Foram confirmados healthcheck interno, HTTP no host, duas instâncias com flags/portas distintas e encerramento independente. Detalhes: docs/DIAGNOSTICO-DOCKER.md. Não enviar evoluções para purple-talent.

## Leia primeiro — estado atual da nova fase (06/11/2026)

Registro histórico de 06/11; a consolidação no início deste arquivo prevalece. O usuário autorizou implementar a nova fase, exigiu formulários no banco (não JSON) e pediu atualizar este arquivo e publicar o conjunto em **Breno-J-Oliveira/salvamento**. Não há autorização nova para enviar estas evoluções a purple-talent. Bancos, chaves e evidências privadas continuam fora do GitHub.

### O que funciona agora

- Landing orientada ao recrutamento; vagas públicas, detalhe e cadastro/login que retorna ao formulário escolhido.
- Perguntas específicas por vaga em editor visual. Persistência relacional em job_form_versions, form_questions, form_options e application_answers. A versão mostrada é assinada/vinculada a usuário e vaga; alteração posterior não muda o significado das respostas.
- Rascunho de candidatura, revisão antes de confirmar, envio único e acompanhamento de status/feedback. Rascunhos não são tratados como candidaturas enviadas pela administração.
- Avaliação simulada por candidatura em três etapas SOC ou AppSec, respostas relacionais e revisão humana. Não há execução de comandos nesses cenários nem reaproveitamento de pontos do treino como nota da seleção.
- Painel da mentoria com respostas/evidências, mudança de etapa, nota interna separada do feedback compartilhado e histórico persistido.
- Gestão editorial de vagas em vacancies.py: criar/editar rascunho, publicar, pausar/reabrir inscrições e encerrar definitivamente. Prévia somente da equipe. Empresa, descrição, área, referência de pontos, nível, modalidade, local e prazo.
- Prazo até o fim do dia escolhido em Brasília (UTC-3), com limite de novas entradas entre 2000 e 2100. Vaga expirada/pausada/encerrada bloqueia novos envios em rotas novas e legadas; candidaturas enviadas continuam avaliáveis. Encerrar não apaga candidaturas. Para nova seleção após encerramento, criar outra vaga.
- Revisão otimista da vaga com409 e campos preservados quando outra aba/pessoa alterou o registro. Rascunho não aparece para candidatos nem em /jobs legado. A área não muda após qualquer candidatura para preservar a coerência da avaliação.

### Estrutura e execução atuais

Flask, SQLite e HTML/Jinja/CSS/JS locais permanecem. app.py integra autenticação, treino e módulos. recruitment.py gerencia formulários/candidaturas; selection.py, etapas seletivas; vacancies.py, ciclo de vagas. Não introduzir outro framework/banco para sofisticar a base. Migrações são incrementais e leem JSON antigo somente para conversão; estruturas legadas são preservadas, sem novas escritas operacionais em JSON.

Aplicação local: .venv/Scripts/python.exe app.py. Demonstração isolada sem Docker: .venv/Scripts/python.exe tests/serve_recruitment.py em http://127.0.0.1:5056. Esse servidor usa output/qa/recruitment-browser.db e vagas fictícias; não é implantação pública nem o banco da equipe. Docker continua necessário somente para a Intranet executável.

### Verificação mais recente desta entrega

- tests/run_report.py: 98 testes Python, 97 aprovados e 1 Docker real opcional ignorado.
- tests/browser_recruitment.cjs:11 cenários Chrome aprovados após integração.
- tests/browser_vacancies.cjs:10 cenários Chrome aprovados; gestão editorial, privacidade de rascunhos, inscrição/pause/reabertura/encerramento, avaliação preservada, conflito409 e390/1440px.
- Revisão independente encontrou datas extremas que quebravam datetime.fromtimestamp no Windows; conversão portátil e validação de intervalo corrigidas e cobertas por teste. Screenshots mobile do editor e vaga encerrada foram inspecionadas.
- Evidências em output/qa são locais/ignoradas. Não apresentar essas verificações como homologação pública ou como teste real de Docker nesta etapa.

### O que ainda falta — ordem sugerida

1. **Avaliação seletiva mais estruturada:** rubrica por competência, notas justificadas por candidatura, revisão final do parecer e cenários mais completos com artefatos. Os cenários atuais são guiados/textuais; não afirmar que simulam SIEM/EDR/Windows reais.
2. **Operação do recrutamento:** busca/filtros e paginação de candidaturas, histórico legível no painel, atribuição de avaliadores e regra de transições de candidatura mais restrita. Hoje o mentor interno realiza toda a gestão.
3. **Jornada do candidato:** desistência pelo próprio candidato, revisão de consentimento/visibilidade, exportação e política de retenção; recuperação de acesso e confirmação de e-mail antes de uso público. Não simular envio de e-mail como serviço real.
4. **Papéis e escopo:** separar administrador, recrutador e avaliador; isolamento por organização/campanha antes de multiempresa. Nunca promover contas automaticamente.
5. **Figma e acessibilidade:** nova página com 26 telas desktop editáveis já criada; layouts móveis, estados de erro mais completos e atualização do design com o editor real de vagas ainda pendentes. Protótipo não autentica ou grava dados do produto. Testes com teclado/leitor de tela e aceite humano continuam necessários.
6. **SEO e implantação:** metadados e noindex privado já básicos. Definir domínio/hospedagem, canonical/sitemap de conteúdo público, páginas de privacidade e operação antes de indexar. Não publicar serviço web externo como consequência de um commit de código.
7. **Operação/segurança:** backup/restauração ensaiados com base representativa, monitoramento, retenção/auditoria, revisão de dependências e capacidade. Locks/rate limiting em memória não coordenam múltiplos processos. Docker precisa reconciliação independente e isolamento adicional para exposição pública.
8. **Expansão posterior:** gestão editorial versionada de desafios, eventos/turmas, busca de talentos por evidências e integrações de contato. Ranking não decide contratação.

Detalhes da entrega atual: docs/ENTREGA-GESTAO-VAGAS.md. Backlog mantido em docs/PROXIMAS-MELHORIAS.md. O restante deste arquivo registra contexto e etapas anteriores; resultados históricos não substituem os acima.


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

## Etapa de maturidade posterior ao salvamento inicial

O usuário pediu priorizar completude e robustez dos sistemas existentes e remover emojis, sem novas features. Pediu análise prévia, revisão do trabalho dos subagentes e integração final. Autorizou publicar a etapa concluída apenas em salvamento. A revisão está em docs/REVISAO-MATURIDADE.md, com frentes de interface e Docker. Foram corrigidos título do dossiê contendo relatos, submissões duplicadas e recuperação por bfcache, limites de campos, pausa/reabertura com estado explícito, consultas repetidas de candidaturas, falhas de persistência e tratamento de respostas inválidas/limpeza Docker. A identidade visual e a stack permanecem.
Validação final desta etapa: 65 testes Python aprovados com Docker real habilitado, zero ignorados; 15 cenários Chrome aprovados. O gerente revisou os diffs das frentes, reexecutou a integração e reiniciou o servidor local. A aplicação continua local, sem homologação de produção. Resultados detalhados em docs/REVISAO-MATURIDADE.md.


## Nova fase de recrutamento — 06/11/2026

Implementação atual acrescenta recruitment.py e selection.py. Vagas públicas em /opportunities, retorno seguro após login/cadastro, formulário próprio da vaga, rascunho, revisão e confirmação, acompanhamento em /my-applications e gestão da mentoria em /admin. O editor de perguntas é visual e envia campos de formulário convencionais.

Por instrução explícita do usuário, formulários ficam em tabelas relacionais SQLite: job_form_versions, form_questions, form_options e application_answers. jobs.current_form_version aponta a versão atual; applications.form_version preserva a versão da inscrição. Token assinado vincula vaga/usuário/versão desde a primeira abertura. JSON só é lido pela migração de dados anteriores; tabelas/colunas legadas ficam preservadas sem uso operacional novo. Etapas e respostas da avaliação também são relacionais: selection_assessments, selection_stages e selection_responses.

Avaliação textual simulada tem três etapas sequenciais SOC ou AppSec, por candidatura, sem pontuar treino. Mentoria recebe evidências, registra etapa, nota interna e feedback compartilhável. Não há envio de e-mails ou contratação automática. Papéis continuam participante e mentor; não há RBAC multiempresa, editor de vagas com todos os estados futuros ou homologação pública.

O usuário autorizou explicitamente publicar esta etapa em Breno-J-Oliveira/salvamento. Nenhuma autorização adicional de publicação em purple-talent foi dada. Não publicar banco, chaves, env, venv ou evidências privadas. Documento de planejamento: docs/PLANO-NOVA-FASE.md; registro Figma: docs/FIGMA-NOVA-FASE.md.

Validação integrada desta etapa: 85 testes Python (84 aprovados, 1 Docker opcional ignorado), 11 cenários Chrome aprovados e migrações relacionais verificadas em bases temporárias. Registro: docs/ENTREGA-RECRUTAMENTO.md.
Atualização de 07/11: Docker real aprovado em 17 testes após estabilização; regressão geral 110 testes, 109 aprovados e 1 opcional Docker ignorado na suíte principal. Histórico de etapas mostra ator e data UTC apenas para mentoria. Acessibilidade do recrutamento recebeu foco em erros, associações aos campos e rótulos contextuais; ver docs/REVISAO-ACESSIBILIDADE-RECRUTAMENTO.md. Testes de leitor de tela com pessoas continuam pendentes.
