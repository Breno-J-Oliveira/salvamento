# Busca e navegação de candidaturas

O painel da equipe agora consulta candidaturas em páginas de 20 registros, por ID decrescente, com busca literal por nome/vaga e filtros de etapa e vaga. Rascunhos continuam excluídos. Os indicadores globais e contagens de inscrição por vaga não são reduzidos pelos filtros.

Busca aceita até 120 caracteres; etapa deve pertencer às etapas conhecidas, exceto rascunho; vaga e página devem ser inteiros positivos limitados. Entradas inválidas recebem 400. Páginas além do fim mostram a última página disponível. Links de navegação preservam os filtros e retornam à seção de candidaturas. Estado vazio e limpeza dos filtros estão disponíveis.

A listagem usa COUNT e LIMIT/OFFSET no SQLite, sem carregar todas as candidaturas no Python. Esse limite é apenas da lista de candidaturas; a gestão de vagas mantém seu comportamento anterior. Não altera permissões, transições ou candidaturas recebidas.

Testes direcionados estão em tests/test_admin_filters.py. A validação integrada do gerente deve confirmar o comportamento no navegador antes de anunciar publicação.
Validação direcionada concluída: 5 testes aprovados, zero falhas, em 400,665 segundos neste host. Sintaxe Python e git diff --check aprovados. Busca, combinações de filtros, links, páginas sem duplicação, exclusão de rascunhos, entradas inválidas e autorização foram exercitados em SQLite temporário.
