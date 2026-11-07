# Continuidade da avaliação seletiva — 7 de novembro de 2026

## Base atualizada

A versão foi baixada de Breno-J-Oliveira/salvamento, commit13f9c2c, em branch codex/continue-salvamento. O checkout anterior foi preservado em codex/before-salvamento-update. Não foram substituídos banco local, chave de sessão ou evidências privadas.

## Revisão por competência

A nova tabela relacional selection_reviews registra quatro competências: investigação, evidências, decisões e comunicação. Cada nota é inteira de0 a5; a justificativa exige30 a4000 caracteres. Somente mentores registram notas, e apenas depois do envio completo da avaliação daquela candidatura.

Cada gravação insere uma revisão com autor, data UTC e versão da rubrica. Uma revisão não altera as anteriores. A revisão esperada é conferida dentro da transação: outra gravação concorrente retorna409 e mantém os campos digitados. O formulário inválido retorna400. Constraints SQLite conferem intervalo das notas e unicidade da revisão.

A interface de candidatura da mentoria mostra formulário e histórico. A escala também está explicada ao candidato no briefing da avaliação. As notas e justificativas continuam internas; feedback compartilhado é um campo separado. Registrar rubrica não altera etapa da candidatura, feedback ou pontos de treino e não aprova candidatos automaticamente.

## Integração e verificação

Arquivos centrais: rubric.py, templates/_rubric.html, templates/rubric_review.html, integração em app.py/admin_application.html e testes em test_rubric.py e browser_recruitment.cjs. A migração é incremental e repetível. Cenários permanecem textuais e educativos, sem executar comandos ou simular SIEM real.

Os resultados finais serão registrados após a regressão. A primeira tentativa de Docker real teve timeout e erro500 do engine durante inicialização; o usuário informou que avisará quando estiver pronto. Isso não constitui aprovação da integração Docker nesta etapa.

## Resultados direcionados de 07/11

Rubrica:7 testes aprovados em SQLite temporário, incluindo autorização, campos inválidos, histórico, conflito409, privacidade, migração repetida e constraints reais. Painel:5 testes de filtros/paginação aprovados. Chrome integrado:13 cenários de recrutamento e10 de gestão editorial aprovados, incluindo rubrica persistida, notas internas ausentes da jornada do candidato, filtros e390/1440px. As capturas mobile do parecer foram inspecionadas.

Após o usuário confirmar a abertura do Docker, ocorreram timeouts transitórios. O diagnóstico isolado confirmou healthcheck interno e HTTP200 no host com as restrições originais. A repetição da bateria real do orquestrador concluiu17/17 testes aprovados, zero ignorados; as duas instâncias foram removidas e nenhum recurso de outro projeto foi alterado. Não houve rebuild, alteração de código Docker ou reinício do daemon. Registro: docs/DIAGNOSTICO-DOCKER.md.

A suíte geral está sendo consolidada separadamente; não confundir os testes direcionados com aprovação de toda a suíte.
Regressão integrada: 110 testes Python executados, 109 aprovados e 1 teste Docker opcional ignorado nessa suíte. Em execução separada, o Docker real passou nos 17 testes. O histórico de etapas foi integrado com ator e data UTC; seus 5 testes direcionados passaram. A revisão de acessibilidade está em docs/REVISAO-ACESSIBILIDADE-RECRUTAMENTO.md.
Regressão final integrada: 14 cenários Chrome aprovados após corrigir seletor de teste ambíguo causado pelos novos rótulos acessíveis. O histórico de etapas foi validado no fluxo e em 5 testes direcionados. A suíte geral executou 110 testes, com 109 aprovados e 1 Docker ignorado; a bateria Docker real separada passou 17/17.
