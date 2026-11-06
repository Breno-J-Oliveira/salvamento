# Próximas melhorias do Purple Talent

Atualizado em 06/11/2026 após a gestão editorial de vagas. O fluxo atual já inclui formulários relacionais por vaga, candidaturas com rascunho/revisão, avaliação textual de 3 etapas, feedback, editor de vagas, prazo e estados. As propostas abaixo ainda não estão concluídas.

1. **Rubrica e parecer por candidatura.** Estruturar critérios/notas justificadas, evidências e revisão antes de compartilhar feedback. Validar que cada nota pertence àquela seleção e que notas internas não vazam.
2. **Busca e acompanhamento administrativo.** Filtros por vaga/etapa, paginação, histórico legível e atribuição de avaliadores; dados autorizados e tempo de consulta verificados com volume representativo.
3. **Jornada e privacidade do candidato.** Desistência, consentimento granular, exportação, retenção e recuperação de conta. Definir dados mínimos e política antes de coletar documentos ou dados sensíveis.
4. **Perfis e organizações.** Separar administração, recrutamento e avaliação; testar acesso cruzado entre vagas/campanhas/organizações antes de multiempresa.
5. **Desafios e trilhas mais completos.** Criar cenários com artefatos correlacionados, rubricas publicadas e editor versionado de conteúdo. Treino e seleção permanecem separados; sem aprovação automática por ranking.
6. **Figma e acessibilidade.** Atualizar o design com o editor real, layouts móveis e erros/estados; validar teclado, leitor de tela e uso humano dos percursos. Protótipo é referência e não funcionalidade operacional.
7. **Operação e segurança.** Backup/restauração ensaiados, monitoramento, capacidade, retenção/auditoria e revisão de dependências. Medir antes de mudar banco/stack. Múltiplos processos exigem coordenação fora da memória local.
8. **SEO e publicação do serviço.** Definir domínio/hospedagem, privacidade, canonical e sitemap somente público; preservar autenticação e noindex de áreas privadas. Um commit não autoriza deploy público.
9. **Integrações futuras.** Comunicação real por e-mail, eventos/turmas e contato mediado, com configuração e consentimento apropriados. Não informar envio ou contratação que não aconteceram.

A base continua Flask, SQLite e Docker CLI no host. Laboratórios ficam separados dos dados da plataforma. Execução arbitrária de código, exposição remota e carga elevada precisam de isolamento e operação adicionais.
