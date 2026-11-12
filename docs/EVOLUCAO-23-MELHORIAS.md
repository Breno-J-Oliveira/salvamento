# Evolução de usabilidade em 12 de novembro de 2026

Esta entrega acrescenta 23 melhorias funcionais verificadas à versão de apresentação. A contagem agrupa controles da mesma função: subir e descer são uma melhoria de reordenação; as diferentes datas são uma melhoria de acompanhamento.

## Editor de formulários

1. Duplicar uma pergunta com identificador novo, preservando configuração.
2. Reordenar perguntas, mantendo a ordem salva e as respostas históricas.
3. Desfazer a última remoção, recuperando posição, opções e gabarito antes de salvar.
4. Prévia local dos seis formatos de resposta, sem mostrar gabarito.
5. Contador de opções e validação dos limites.
6. Contador de caracteres nos textos das perguntas.
7. Aviso de alterações não salvas ao sair da página.

## Jornada do candidato

8. Busca de vagas por cargo, empresa, descrição ou local.
9. Filtro de vagas por área.
10. Filtro de modalidade combinado com busca e área, com estado vazio e limpeza.
11. Datas de início, envio e última gravação em horário de Brasília.
12. Histórico da própria candidatura com etapas e datas.
13. Resumo do progresso e da próxima ação por candidatura.
14. Extrato protegido e imprimível das respostas da versão preenchida.
15. Filtro das próprias candidaturas por etapa.
16. Prazo de novas inscrições visível, distinguindo fechamento da vaga de cancelamento de candidatura já enviada.

## Laboratórios

17. Descrições e abordagens corretas para exploração web e investigação de incidente, sem chamar o console de intranet.
18. Indicação de instâncias da própria conta, excluindo expiradas e dados de terceiros.
19. Resumo da quantidade de ambientes registrados em relação ao limite individual.
20. Contagem regressiva de validade das instâncias registradas.
21. Ação contextual para abrir, rever ou gerenciar o ambiente.
22. Sinalização de desafios concluídos pela conta autenticada.
23. Busca dos laboratórios com normalização de acentos e estado vazio.

## Verificação

- Testes novos: 7/7 da jornada e extrato; 3/3 de privacidade, estado e resultado dos laboratórios.
- Revisão QA independente: 3/3 regressões de editor/gabarito/tokens e 3/3 testes de extrato; leitura dos novos fluxos de autorização e serialização.
- Chrome real: 18/18 cenários integrados em tests/browser_recruitment.cjs, incluindo os filtros combinados, extrato em impressão e laboratórios.
- Editor no Chrome: duplicação, identificadores únicos, ordem persistida, desfazer com gabarito, limite de 15 perguntas, prévia dos formatos, aviso ao sair e contadores. Capturas móveis e desktop verificadas.
- Smoke visual independente: oito telas em 390 e 1440 px, com título sem espaços e URL longa; sem transbordamento ou erros JavaScript. Extrato também conferido em mídia de impressão.
- Sintaxe JavaScript e git diff --check aprovados.

As evidências sintéticas ficam em D:/purple-talent-qa, fora da publicação. A suíte completa da etapa anterior não é apresentada como reexecutada nesta etapa; as verificações acima cobrem os fluxos alterados. O estado do Docker é confirmado no desafio, não inferido apenas de um registro no banco.

## Preservação e limites

Sem novas dependências, alteração de credenciais ou limpeza do banco da equipe. Extratos não carregam notas internas ou gabaritos. O servidor continua local; os limites de produção e segurança descritos em ENTREGA-APRESENTACAO.md permanecem aplicáveis.
