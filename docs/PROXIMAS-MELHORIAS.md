# Próximas melhorias do Purple Talent

As propostas abaixo são evolução futura. Não fazem parte das funcionalidades já implementadas.

| Prioridade | Proposta | Valor e critério de aceite |
| --- | --- | --- |
| 1 | Rodadas Purple Team com rubrica e feedback | Registrar ataque, evidência defensiva e mitigação em uma rodada, com revisão humana e critérios publicados antes do evento. |
| 2 | Eventos e turmas | Separar participantes, desafios e rankings por campanha; impedir que um recrutador consulte dados de outra campanha sem permissão. |
| 3 | Busca de talentos por evidências | Filtrar candidatos por desafios resolvidos, categoria, relatos e notas da mentoria, distinguindo habilidades declaradas de resultados observados. |
| 4 | Trilhas com pré-requisitos e recomendações | Sugerir o próximo desafio a partir do progresso, explicar a recomendação e permitir que o participante escolha outro percurso. |
| 5 | Gestão editorial de desafios | Mentor cria versões de conteúdo, valida respostas em ambiente de teste e publica sem alterar retroativamente a pontuação de quem já concluiu. |
| 6 | Provisionamento assíncrono e controle de capacidade | Ao evoluir para várias máquinas/processos, persistir solicitações de laboratório, aplicar quotas atomicamente e reconciliar expiração mesmo sem processo web ativo. |
| 7 | Operação e recuperação | Estabelecer backup e restauração testados, monitoramento de falhas e trilha de auditoria com retenção e acesso definidos. |
| 8 | Privacidade e recrutamento | Adicionar consentimento granular para exibição do perfil, contato mediado e exportação de dados; confirmar o escopo dos dados antes de qualquer exclusão. |

## Escalabilidade

A versão local conserva Flask, SQLite e Docker. A agregação do ranking e os índices reduzem o custo de consulta. Antes de oferecer acesso remoto ou suportar vários processos, devem ser medidos usuários simultâneos, latência e bloqueios de escrita. Essa medição orientará paginação, limites de recursos, execução assíncrona e eventual evolução de persistência. O lock em memória e o contador de tentativas atual não coordenam múltiplos processos.

Laboratórios precisam continuar separados dos dados da plataforma. Execução de código arbitrário e exposição pública exigem um desenho de isolamento distinto do laboratório HTTP educativo atual.
