# Gestão editorial de vagas — entrega de 06/11/2026

O novo módulo vacancies.py acrescenta editor de vagas em /admin/jobs/new e /admin/jobs/<id>/edit, prévia exclusiva da equipe e ações de estado com CSRF, autorização e revisão do registro. A identidade visual e a stack atuais foram preservadas.

## Regras implementadas

- Rascunho fica restrito à equipe e pode ser preparado com título/área antes da publicação. Empresa e descrição completas são exigidas ao publicar.
- Estados publicados: rascunho, publicada, pausada e encerrada. Uma pausa permite reabertura com prazo válido; encerramento é definitivo. Nenhuma ação apaga candidaturas.
- Prazo opcional até o fim do dia escolhido no horário de Brasília UTC-3; o fim exclusivo é meia-noite do dia seguinte. Novas datas aceitas entre 2000 e 2100. A conversão para exibição independe dos limites de timestamp do Windows.
- Nível, modalidade e local são campos da vaga. Mudança de área fica bloqueada após qualquer candidatura, inclusive rascunho, para preservar o sentido da avaliação.
- Revisão otimista com409 evita sobrescrever dados de outra aba/pessoa. O formulário preserva valores digitados e oferece recarregar o registro atual. Mudanças são registradas em job_history, sem respostas pessoais no histórico editorial.
- Inscrições verificam estado/prazo no servidor, inclusive confirmação, formulário e rotas legadas. Rascunhos não vazam por /jobs de participante. Encerradas e expiradas mantêm página informativa sem CTA de inscrição; pausadas/rascunhos não têm detalhe público.
- Avaliações seletivas de candidaturas já enviadas continuam após fechar as inscrições.

## Persistência e atualização

A migração adiciona colunas editoriais na tabela jobs e cria job_history. Vagas antigas active=1 tornam-se publicadas; active=0 tornam-se pausadas. Formulários e respostas continuam nas tabelas relacionais da entrega anterior. O banco real da equipe não foi necessário para QA e não deve ser apagado para atualizar. Antes de aplicar migrações a dados reais, manter backup e testar em cópia.

## Evidências executadas

- 98 testes Python: 97 aprovados e 1 teste de Docker real opcional ignorado.
- 11 cenários de regressão Chrome do recrutamento aprovados.
- 10 cenários Chrome de gestão editorial aprovados, incluindo criação privada, prévia, publicação, inscrição, pausa/reabertura, encerramento com avaliação preservada e conflito de edição.
- Verificações de 390/1440px e capturas mobile do editor e detalhe encerrado inspecionadas.
- Revisão independente reproduziu quebra com datas extremas no Windows; corrigida com conversão portátil, intervalo validado e teste de regressão.

Comandos: .venv/Scripts/python.exe tests/run_report.py; tests/serve_recruitment.py deve estar ativo em 5056 para os scripts tests/browser_recruitment.cjs e tests/browser_vacancies.cjs. Playwright é ferramenta de QA, não dependência do produto. Evidências privadas permanecem em output/qa e são ignoradas no Git.

## Pendências

Este é um sistema local de demonstração. Papéis separados, multiempresa, recuperação de conta, e-mail, hospedagem pública, testes operacionais de backup/carga e revisão de privacidade continuam pendentes. O backlog atualizado está em PROXIMAS-MELHORIAS.md e no início de claude.md. Não confundir aprovação dos testes com aceite humano ou homologação de produção.
