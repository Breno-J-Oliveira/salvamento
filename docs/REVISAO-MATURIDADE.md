# Revisão de maturidade e integração

Data: 6 de novembro de 2026. Objetivo: melhorar os sistemas existentes, sem expandir o catálogo ou trocar a arquitetura.

## Análise realizada antes das alterações

A revisão encontrou falhas concretas em recuperação e consistência: relatos de aprendizagem apareciam indevidamente no título da aba do dossiê; formulários voltavam bloqueados pelo cache de navegação; confirmação e carregamento não eram coordenados; notas e senha tinham limites inconsistentes entre interface e servidor; pausa de vaga invertia estado a cada repetição; a página de vagas consultava candidatos uma vez por vaga; respostas inválidas da CLI Docker e falha durante limpeza podiam gerar erros inadequados; indisponibilidade do SQLite não recebia orientação de recuperação.

## Integração e revisão do gerente

A frente de interface alterou templates e JavaScript. O gerente conferiu o título do dossiê, o token CSRF preservado, o estado explícito de pausa/reabertura, a restauração em pageshow e a região acessível dos filtros. A frente Docker alterou apenas orquestração e testes. O gerente conferiu validação de rede/porta, limites das chamadas, propriedade dos containers e preservação do erro original quando a limpeza falha.

Na integração, o teste de indisponibilidade revelou outra falha: uma sessão sem nome causava erro no próprio template de recuperação. A base agora usa identificação alternativa para essa condição, sem invalidar a sessão ou solicitar novos dados.

O backend passou a responder 503 com Retry-After para banco ocupado e 500 controlado para outra falha de persistência, sem mostrar mensagens internas ao usuário. Formulários de vaga enviam o destino ativo/inativo e o servidor aplica esse destino, sem inverter novamente em reenvio. O endpoint antigo sem esse campo mantém compatibilidade com os clientes existentes. A listagem da mentoria carrega candidaturas numa única consulta, eliminando a consulta adicional por vaga.

Emojis e marcadores decorativos foram removidos da interface e das mensagens da aplicação, sem mudar as fontes ou a identidade visual. As referências gráficas originais permanecem como material de projeto.

## Evidências e limites

As frentes registram seus testes em REVISAO-INTERFACE.md e REVISAO-DOCKER.md. A regressão integrada usa bancos temporários, Chrome e Docker real. Não foram efetuadas alterações destrutivas, troca de credenciais ou implantação de produção. Locks e limitação de tentativas continuam locais ao processo; a arquitetura não foi convertida em serviço distribuído.

O resultado final e a publicação em salvamento são registrados no histórico de mudanças depois da execução. A publicação não inclui banco, segredos ou evidências privadas e não altera purple-talent.

## Resultado integrado

Suíte final `tests/run_report.py` com RUN_DOCKER_TESTS=1: 65 testes aprovados, zero falhas e zero ignorados, incluindo Docker real. Chrome: 15 cenários aprovados, com permissões, persistência, relatórios, responsividade, cadastro e ciclo de laboratório. Os quatro testes novos de maturidade também foram reexecutados isoladamente e passaram. O teste de recuperação de sessão inicialmente revelou a falta de fallback no nome, que foi corrigida antes da última suíte completa.

O gerente conferiu os diffs das duas frentes. Sintaxe Python/JavaScript, varredura de emojis no código/textos ativos e git diff --check aprovados. O servidor local foi reiniciado e respondeu HTTP200. A publicação desta etapa é exclusivamente em salvamento; purple-talent não recebe as melhorias.
