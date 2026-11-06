# Purple Talent — planejamento da fase de recrutamento

Data: 06/11/2026. Status: proposta de implementação, sem alteração funcional ou publicação.

## Base e direção

Leitura realizada: claude.md, README.md, app.py (rotas, schema, autenticação e oportunidades), catalog.py, learning.py, templates de cadastro, navegação e vagas, documentação de maturidade e próximas melhorias. A base atual usa Flask, SQLite, Jinja, CSS/JS e Docker CLI no host. Preservar stack, visual de referência e dados existentes.

Existem 12 desafios, cadastro/login, perfil básico, oportunidades com criação/pausa, candidatura única, avaliações humanas, ranking, dossiê e relatos. A candidatura atual registra apenas vaga, usuário e data. Não há formulário específico, etapas de seleção ou avaliação isolada por candidatura. Os resultados globais de treino não constituem uma avaliação controlada por vaga.

Direção: uma plataforma de seleção por evidências. A unidade central passa a ser a candidatura de uma pessoa a uma vaga; conta, treinamento e candidatura são conceitos distintos. Não decidir contratação automaticamente por pontuação ou velocidade.

Premissas: “Ceo do site” significa SEO; confirmar antes de implementar essa frente. Primeira versão atende uma organização com equipe interna. Operação multiempresa, publicidade e domínio público exigem escopo separado. Figma significa consolidar os fluxos e telas na identidade existente; edição remota depende da identificação do arquivo de destino.

## Jornada principal

1. Visitante entende a proposta na landing e consulta vagas abertas publicamente.
2. Escolhe vaga e vê requisitos, etapas, critérios, prazo e uso das informações.
3. Cria conta ou entra; após autenticar, retorna à vaga escolhida.
4. Preenche o formulário daquela vaga, pode salvar rascunho e revisar antes de enviar.
5. Recebe confirmação e acompanha sua candidatura e próximas ações.
6. Executa a avaliação vinculada à candidatura e entrega evidências/relatório.
7. Avaliador revisa pela rubrica publicada; recrutador registra a decisão humana e o feedback compartilhável.

Pessoa já cadastrada não deve repetir cadastro ou misturar respostas entre vagas. Login autentica; o formulário pertence à candidatura e aparece no percurso iniciado pela vaga. Dados comuns do perfil podem ser reaproveitados, com confirmação do candidato.

## Frentes e critérios de aceite

### 1. Vagas e administração — prioridade essencial

Evoluir o cadastro atual para rascunho, publicada, pausada e encerrada; incluir senioridade, modalidade, local, descrição, prazos, formulário e trilha de avaliação. Administração lista candidaturas por vaga, filtra por etapa e abre respostas/evidências. Transições propostas: rascunho de candidatura, enviada, em avaliação, entrevista, aprovada, não selecionada e desistência. Regras de transição e histórico precisam ser definidos no servidor.

Aceite: recrutador publica uma vaga completa, candidato consegue encontrá-la, vaga pausada/encerrada recusa novas submissões, encerramento não apaga candidaturas, decisões registram autor/data e candidato não acessa notas internas.

### 2. Formulários por vaga — prioridade essencial

Editor inicial limitado a texto curto/longo, seleção única/múltipla, número e URL; campo com identificador estável, rótulo, ajuda, obrigatoriedade, limites e opções. Evitar lógica condicional arbitrária e upload de currículo no primeiro corte. Exemplos: SOC pede disponibilidade e relato de investigação; AppSec pede experiência em revisão de código e link de projeto.

Publicação cria uma versão do formulário. Candidatura aponta para essa versão; alterar perguntas não reinterpreta respostas anteriores. Definir política explícita para rascunhos quando a vaga muda. Validar campos, tipos e opções no servidor e rejeitar campos inesperados.

Aceite: duas vagas apresentam perguntas diferentes; resposta obrigatória ausente impede envio; rascunho persiste após sair/entrar; reenvio não duplica candidatura; administrador lê exatamente as perguntas e respostas enviadas naquela versão.

### 3. Avaliação prática em fluxo — prioridade essencial após candidatura

Criar trilhas com etapas, pré-requisitos, briefing, artefatos, evidências e critérios. Primeiro cenário sugerido: incidente SOC — investigar autenticação, correlacionar eventos, montar linha do tempo, justificar contenção e escrever relatório. Segundo: AppSec — reconhecimento em alvo autorizado, identificação de falha, demonstração controlada, correção proposta e validação defensiva.

Complexidade deve vir de investigação e decisões justificadas. Definir nível, pré-requisitos e limite de esforço por vaga; manter aquecimento. Separar prática livre de tentativa seletiva: treino não recebe retroativamente nota de seleção. Registrar versão do desafio/rubrica e instante de início da avaliação. Feedback de treinamento pode revelar solução; avaliação seletiva exige política própria de dicas e respostas.

Aceite: primeira trilha com pelo menos três etapas relacionadas, desbloqueio validado no servidor, progresso retomável, evidência por etapa, submissão final e revisão humana. Avaliações de vagas distintas não compartilham resultados por acidente.

### 4. Landing e SEO — prioridade de apoio

Explicar proposta, público, funcionamento, vagas, avaliação, privacidade e próximos passos; CTAs distintos para explorar vagas e entrar. Diferenciar evidências reais de exemplos. Usar dados reais ou nenhuma métrica promocional.

Planejar títulos e descrições por página, HTML semântico, navegação acessível, URLs estáveis de vagas, sitemap apenas público, canonical e conteúdo compartilhável. Perfis, formulários, resultados e admin ficam autenticados e fora da indexação; robots não substitui autorização. Dados estruturados de vaga somente quando os campos e a oferta publicada os sustentarem. Não prometer posicionamento em busca.

Aceite: visitante entende como participar sem login, abre detalhe público de vaga; teclado/mobile funcionam; páginas privadas não vazam conteúdo e não entram no sitemap. SEO público depende da futura hospedagem/domínio.

### 5. Segurança — transversal, bloqueante para exposição pública

Preservar CSRF, hash de senha, validação, consultas parametrizadas, rate limiting e sessões existentes. Planejar autorização por ação e recurso: administrador gerencia acesso, recrutador gerencia processos autorizados, mentor avalia atribuições e candidato acessa apenas seus dados. Migração dos mentores existentes precisa de mapeamento explícito; não conceder novos poderes automaticamente.

Incluir auditoria de mudanças/decisões sem conteúdo sensível, tratamento de erro, backup e restauração testados. Minimizar coleta, distinguir informações obrigatórias/opcionais, definir visibilidade e retenção. Evitar CPF, dados sensíveis e documentos sem necessidade demonstrada. Recuperação de acesso e confirmação de e-mail entram antes de serviço público real; não criar envio fictício de e-mails.

Aceite: testes de troca de IDs, elevação de papel, leitura indevida, submissão forjada e versões inválidas; restauração verificada em cópia. Laboratórios nunca recebem banco, credenciais administrativas ou socket Docker. Novos alvos exigem validação de isolamento e capacidade.

### 6. Figma e integração

Desenhar primeiro detalhe de vaga, autenticação com retorno, formulário, acompanhamento, editor de vaga/formulário e ficha administrativa. Cobrir vazio, carregamento, erro, validação, sucesso, mobile e foco por teclado. Reutilizar referências e componentes visuais atuais.

Aceite: fluxo completo revisável antes de construir telas secundárias. Integração E2E: publicar vaga -> cadastrar candidato -> enviar formulário -> concluir trilha -> mentor revisar -> recrutador registrar decisão -> candidato visualizar status permitido. Testar sem Docker nas partes independentes e com Docker real nos alvos aplicáveis.

## Modelo e organização propostos

Manter users para identidade e perfil comum; jobs para oportunidade. Acrescentar versões de formulário/perguntas, respostas da candidatura, estado/histórico, versões da trilha/etapas, tentativas seletivas/evidências e avaliações vinculadas à candidatura. Usar chaves estrangeiras, índices e transações adequados, incluindo unicidade por pessoa/vaga no primeiro corte. Não alterar destrutivamente tabelas ou reavaliar resultados antigos.

Arquivos atuais: app.py concentra autenticação, vagas, candidaturas e avaliação; catalog.py fornece o catálogo; learning.py fornece progresso/relatos; orchestrator.py controla o ciclo Docker. templates e static compõem a interface; tests contém regressão Python, navegador e Docker opcional. Como a mudança crescerá, extrair recrutamento/formulários em módulos pequenos, sem reescrita geral ou novos serviços.

## Ordem de execução para hoje

1. Fechar papéis, estados, perguntas de duas vagas exemplo e rubrica da primeira trilha. Responsável: coordenação/produto. Saída: critérios e exemplos verificáveis.
2. Preparar migração incremental e candidatura/formulário versionados. Responsável: backend/dados, dono exclusivo das migrações e módulos de domínio. Depende de 1.
3. Desenhar e implementar vaga pública, retorno após login e formulário com rascunho. Responsável: frontend, dono de templates/static dessa fatia. Contrato de 2 acordado antes da integração.
4. Integrar editor administrativo mínimo e visualização das candidaturas/respostas. Responsável: backend, interface coordenada sem edição concorrente dos mesmos arquivos. Depende de 2/3.
5. Entregar uma trilha completa vinculada à candidatura e revisão humana. Responsável: coordenação/backend. Depende do vínculo de candidatura estável.
6. Revisão independente, testes E2E, permissões, acessibilidade, backup e documentação. Responsável: QA/revisão, coordenador integra e decide aceite.
7. Completar landing e SEO técnico básico conforme capacidade restante. Publicação permanece fora do escopo autorizado desta fase.

Meta de hoje: uma fatia vertical demonstrável do recrutamento. Se houver restrição de tempo, reduzir quantidade de trilhas e refinamento editorial, preservando autorização, persistência e integridade. As oito frentes não têm esforço equivalente; não prometer concluí-las integralmente hoje.

## Maturidade seguinte

Priorizar acompanhamento de status, feedback humano estruturado, separação de notas internas, histórico de decisões e versões das avaliações. Depois: comparação por competências da mesma vaga, revisão anonimizada quando viável, atribuição de avaliadores, paginação e operação/backup. Mais tarde: banco de talentos com adesão explícita, comunicação por e-mail, relatórios exportáveis, multiempresa e provisionamento independente do processo web. Evitar seleção automática por ranking geral ou detecção de fraude sem evidência confiável.

## Verificação e limites

Este planejamento deriva de leitura do código e documentação; nenhuma suíte foi executada nesta etapa. Os 65 testes Python e 15 cenários Chrome descritos no histórico são resultados anteriores. Reexecutar a regressão disponível antes/depois das mudanças, adicionar testes dos novos contratos e usar banco temporário para QA.

Antes de migrar dados reais, testar em cópia e validar backup/restauração. Rollback de aplicação só é seguro com schema compatível; migrações que alterem dados podem exigir correção adiante. Não apagar banco para atualizar. Não publicar código ou criar commits/PRs nesta etapa: o contexto limita publicações e este pedido solicita planejamento.
