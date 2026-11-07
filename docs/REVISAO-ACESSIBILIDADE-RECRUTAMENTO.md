# Acessibilidade do recrutamento — revisão de 07/11/2026

Escopo limitado ao formulário, revisão, acompanhamento do candidato, macros e CSS de recrutamento. Não houve redesign, dependência nova ou alteração do backend.

## Achados e ajustes

- Campos obrigatórios para envio não tinham estado assistivo de obrigatoriedade. Inputs, selects e textareas agora expõem aria-required, sem impor required HTML: salvar rascunho incompleto continua possível.
- Grupo multiselect inválido não expunha aria-invalid. Fieldset ganhou identificação, erro associado e orientação explícita quando ao menos uma opção é necessária.
- Resumo de erros tinha tabindex, mas não recebia foco nem levava aos campos. Agora usa autofocus, nome acessível e links para os controles ou grupos correspondentes; erros gerais continuam texto sem link artificial.
- Revisão de respostas ganhou retorno direto ao formulário.
- Links repetidos de Minhas candidaturas ganharam contexto assistivo com o título da vaga, preservando os textos visíveis e os destinos.
- Âncoras de erro receberam margem de rolagem e indicação de foco. Cores, fontes e organização foram preservadas.

## Verificação

Todos os quatro templates alterados compilaram com Jinja. Chrome real com HTML renderizado pelos templates: foco inicial no resumo, clique e navegação por Tab/Enter até o campo, aria-required/invalid/describedby, respostas preservadas, rascunho sem bloqueio HTML required, nomes contextuais e retorno de revisão passaram. Viewport390px sem overflow horizontal; captura local inspecionada. Nenhuma exceção JavaScript. git diff --check aprovado.

O teste usou dados sintéticos e DOM renderizado, sem banco da equipe ou reinício do servidor5056. Roteiros/capturas em output/qa são ignorados. A regressão HTTP integrada deve ser executada pelo gerente após atualizar o cache de templates do servidor. Não foi feita auditoria Lighthouse/axe ou avaliação com leitor de tela; estes resultados não constituem certificação WCAG.
