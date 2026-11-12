# Roteiro de demonstração — Purple Talent

## Preparação

1. Execute `.venv\Scripts\python.exe app.py` e abra http://127.0.0.1:5000.
2. Para o console final, aguarde o engine Linux do Docker Desktop e reconstrua as imagens quando o código do laboratório mudar: `docker build -t cti-lab/web-01 challenges/web-01` e `docker build -t cti-lab/incident-01 challenges/incident-01`.
3. Use uma conta de candidato de demonstração, sem informações pessoais reais. Use uma janela separada para a equipe avaliadora, evitando trocar de papel durante o percurso.
4. O acesso local demonstrativo de equipe está descrito no README. Não use essas credenciais em implantação pública.

## Percurso sugerido — 10 a 15 minutos

1. **Problema e proposta:** mostre a landing. Explique que a seleção reúne respostas, análise de artefatos e revisão humana; o ranking público não aprova nem elimina pessoas.
2. **Equipe:** crie uma vaga como rascunho. Configure uma pergunta de texto, uma de conhecimento técnico com escolha única e gabarito opcional e uma de múltipla escolha. Exemplo objetivo: perguntar qual campo permite correlacionar duas requisições, oferecendo request ID como alternativa correta. Não use gabarito para classificar perfil pessoal ou disponibilidade. Confira a prévia e publique.
3. **Candidato:** abra a vaga em outra janela, crie a conta, preencha o formulário, salve o rascunho, recarregue e confirme que as respostas permanecem. Revise e envie.
4. **Avaliação:** abra a avaliação específica da candidatura. Apresente o dossiê de evidências; registre hipóteses, limitações e decisões nas três etapas. Os cenários são sintéticos e não oferecem gabarito ao candidato.
5. **Equipe:** consulte respostas e resultado das questões objetivas, registre a rubrica com justificativa e um feedback compartilhável. Mostre o histórico e a diferença entre nota interna e feedback.
6. **Candidato:** consulte o feedback. Demonstre desistência apenas em uma candidatura descartável, pois a operação encerra a participação e preserva o histórico.
7. **Console isolado:** abra o desafio final, inicie o ambiente e consulte acessos, eventos, processos, conexões e mudanças. Mostre como correlacionar fontes, sem revelar uma solução durante a demonstração. Encerre o container ao finalizar.
8. **Integridade:** explique os avisos de conflito quando outra aba altera respostas, perguntas ou parecer. Mostre o relatório de verificação atual, sem apresentar resultados históricos como testes desta versão.

## Recuperação

O banco e a chave de sessão não são arquivos de demonstração descartáveis. Não apague `lab.db` para corrigir a aplicação. Use a ferramenta de backup documentada no relatório de segurança para criar uma cópia com destino novo; ensaie restauração em outro arquivo antes de qualquer troca operacional.

## Limites que devem ser apresentados com clareza

Esta entrega é uma aplicação local demonstrável. Os laboratórios representam capturas fictícias, sem ataque à infraestrutura da empresa. Operação pública ainda exige hospedagem, HTTPS, provisionamento seguro de equipe, política de dados, recuperação de acesso e validação de capacidade. Nenhum teste comprova invulnerabilidade, e a decisão de contratação permanece humana.
