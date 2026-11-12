# Análise de melhorias até a apresentação de 19/11/2026

> Planejamento anterior à implementação. Para o estado integrado e verificações posteriores, consulte [ENTREGA-POLIMENTO-19.md](ENTREGA-POLIMENTO-19.md).

Análise em 12/11/2026 da versão `Breno-J-Oliveira/salvamento`, commit `9ee1201`. Este documento propõe trabalho; não registra implementação ou aprovação de testes. Revisão de produto e interface independentes, leitura de código/documentos e inspeção de capturas da landing em 1440 e 390 px. Não houve teste de compreensão com usuários, auditoria completa de acessibilidade ou execução da suíte nesta análise.

## Diagnóstico

A plataforma já tem valor demonstrável: formulários relacionais versionados, rascunho/revisão, proteção de conflitos, avaliação por candidatura, rubrica humana, filtros/paginação administrativa, histórico, extrato e desistência. Esses itens não são novidades propostas.

O principal problema de apresentação é tornar esse valor perceptível. A landing tem identidade coerente, mas muitos blocos de texto, uma única ilustração abstrata e pouca prova visual do produto. Em 390 px, a navegação tem links pequenos e rolagem horizontal; a página se torna longa. A aparência precisa de composição e hierarquia, além de novas imagens.

O ambiente atual tem cerca de 5,3 GB livres no C:, está sem Docker e iniciou com banco novo. Conteúdo demonstrativo e execução reproduzível são tão importantes quanto o visual. A versão atual roda numa cópia separada em `.runtime/salvamento-atual`; o incidente de iniciar a versão antiga justifica um comando de execução inequívoco.

## Direção visual

Recomendação: linguagem editorial de investigação, mantendo fundo roxo quase preto, violeta de destaque, Jakarta nos títulos e Inter no texto. Uma imagem principal marcante, capturas verdadeiras do fluxo e telas operacionais discretas. Imagens comunicam contexto; capturas demonstram funcionamento. Não usar telas inventadas como produto real, depoimentos fictícios, empresas parceiras presumidas ou métricas sem medição.

Alternativas: A) investigação editorial, recomendada, equilibra presença humana e evidências; B) produto em destaque, mais sóbria e com capturas maiores, favorece compreensão; C) arena técnica, com logs e linguagem de CTF, apropriada para páginas de treino, mas menos adequada como mensagem principal de recrutamento. Combinar A no hero e B na apresentação das funcionalidades.

## Backlog proposto

Prioridade A: núcleo recomendado antes da apresentação. B: alto valor, selecionar conforme capacidade. C: após a apresentação ou apenas se todo o núcleo estiver estável. Esforço P/M/G é relativo: pequeno, médio e grande; inclui integração, não é promessa de prazo. A lista é um conjunto de opções, não compromisso de concluir tudo em sete dias.

### Aparência e página inicial

1. **Hero mais direto — A/P.** Preservar a mensagem de investigação, reduzir o parágrafo e explicitar público/resultado. Uma ação principal para vagas, uma secundária. Aceite: colegas entendem proposta e próximo passo após dez segundos.
2. **Arte principal original — A/M.** Ilustração editorial de análise de evidências e decisão humana, com recortes desktop/mobile. Conceito gerado nesta análise, ainda sem integração. Aceite: funciona pequena, não corta o assunto e não contém texto essencial.
3. **Capturas reais do produto — A/M.** Mostrar formulário, evidências, rubrica e feedback com dados sintéticos. Aceite: visitante consegue relacionar promessa e telas reais; nenhum dado privado aparece.
4. **Nova ordem da landing — A/M.** Hero, produto em uso, jornada, públicos/evidências, FAQ, chamada final. Reduzir repetições entre benefícios e demais explicações. Aceite: cada seção acrescenta informação distinta.
5. **Vagas abertas na landing — B/M.** Exibir até três oportunidades realmente abertas, consultando estado/prazo com as mesmas regras da listagem. Aceite: se não houver vaga, omitir bloco; sem inventar ofertas.
6. **Família de imagens secundárias — B/M.** Criar imagens coerentes para candidato investigando, equipe avaliando e laboratório sintético. Aceite: uso em pontos de orientação, sem imagem em todo card e sem mudança de estilo entre telas.
7. **Sistema visual consistente — A/M.** Rever espaçamento, largura de leitura, tamanhos de títulos, pesos de botão, bordas e estados usando tokens existentes. Evitar refatoração ampla do CSS histórico. Aceite: telas principais parecem partes do mesmo produto.
8. **Ícones por finalidade — B/P.** Conjunto vetorial local para vagas, evidências, avaliação e treino; manter texto junto do ícone. Aceite: ícones distinguíveis, sem depender apenas de cor.
9. **Rodapé com informação útil — B/P.** Acrescentar atalhos e contexto acadêmico verdadeiro; privacidade somente com informação/página real. Aceite: sem links vazios nem parceria presumida.
10. **Imagens leves — A/P.** Exportar WebP/AVIF e fallback quando necessário, dimensões explícitas e carregamento adiado abaixo da dobra. Ponto inicial: hero até aproximadamente 300 KB, demais até 150 KB, ajustando após inspeção de qualidade. Aceite: arte legível, sem salto de layout e sem download da fonte PNG de 1,6 MB como padrão.

### Navegação e jornada do candidato

11. **Menu por intenção e mobile acessível — A/M.** Destacar vagas/como funciona, agrupar treino e materiais. Menu móvel com controles acessíveis. Aceite: links localizáveis por teclado/toque, sem depender da rolagem horizontal atual.
12. **Entrar visível no cabeçalho — A/P.** Hoje o visitante encontra Criar perfil no header, enquanto Entrar depende do contexto. Aceite: ambos acessíveis em todas as telas públicas relevantes.
13. **Login/cadastro alinhados a recrutamento — B/M.** Rever conteúdo de terminal/CTF e usar arte secundária; preservar retorno à vaga. Aceite: usuário sabe qual processo vai retomar; formulário tem prioridade no celular.
14. **Mostrar/ocultar senha — B/P.** Botão acessível, com estado anunciado e sem enviar formulário. Aceite: funciona com teclado e mantém foco.
15. **Destino após login conforme contexto — A/M.** Preservar `next` seguro; sem destino, candidato chega a candidaturas/próxima ação e mentor ao painel. Aceite: login geral não desvia seleção para treino.
16. **Cards de vagas comparáveis — B/M.** Priorizar cargo, empresa, local/modalidade e prazo; resumo menor e CTAs alinhados. Aceite: três vagas comparáveis sem leitura de descrições inteiras.
17. **Preparação antes do formulário — B/M.** Informar quantidade real de perguntas, rascunho, revisão e o que preparar; não inventar duração. Aceite: dado corresponde à versão do formulário aberta pelo candidato.
18. **Uma próxima ação por candidatura — A/M.** Organizar card atual, que reúne datas, prazo, progresso, extrato, avaliação, desistência e histórico. Aceite: ação principal fica inequívoca, com histórico e ações secundárias preservados.
19. **Estados explicados — B/P.** Acrescentar descrição curta de quem deve agir em cada etapa. Aceite: em revisão não parece uma tarefa pendente do candidato; sem promessa de retorno em prazo inexistente.
20. **Resumo de confirmação para ações definitivas — B/M.** Refinar avisos já existentes de etapa seletiva, desistência e encerramento de vaga. Aceite: efeito e alvo explícitos, sem perder texto preenchido, com foco e cancelamento corretos.

### Avaliação e operação interna

21. **Painel com pendências acionáveis — B/M.** Contagens reais de candidaturas aguardando revisão e links aos filtros correspondentes. Aceite: totais conferem, rascunhos não contam como envios e avaliação ainda em andamento é distinta de pronta para revisão.
22. **Ficha com navegação por seções — B/M.** Âncoras para respostas, avaliação, rubrica, histórico e feedback. Aceite: avaliador chega ao trecho desejado sem percorrer toda a página; notas internas continuam privadas.
23. **Transições de candidatura mais restritas — C/G.** Definir matriz de mudanças permitidas e validar no servidor, considerando candidaturas antigas e avaliações em andamento. Aceite: não voltar a estados incoerentes nem bloquear processos legítimos. Exige regras acordadas e regressão.
24. **Conteúdo de vaga estruturado — C/G.** Responsabilidades, requisitos e diferenciais em campos simples, preservando descrições antigas. Aceite: edição/publicação/legado e migração funcionam sem perder texto. Não adicionar apenas por aparência antes do prazo.

### Acessibilidade, estabilidade e demonstração

25. **Base demonstrativa separada e reproduzível — A/M.** Duas vagas fictícias e candidaturas em estados úteis, com avaliações e feedback sintéticos. Reutilizar o servidor/fixtures existentes onde possível. Aceite: comando explícito, base separada, sem popular banco da equipe automaticamente.
26. **Iniciar e identificar a versão certa — A/P.** Launcher com caminho inequívoco e diagnóstico local de commit, porta, dependências e base selecionada. Não imprimir dados/segredos. Aceite: não repetir o episódio da cópia antiga.
27. **Percurso principal independente de Docker — A/P.** Adaptar roteiro existente para 7–10 minutos: vaga, formulário, candidatura, evidências, rubrica e feedback. Docker como extensão opcional. Aceite: apresentação completa com Docker ausente e sem prometer laboratório ativo.
28. **Passagem de acessibilidade e projeção — A/M.** Teclado, foco, zoom de 200%, contraste medido, texto secundário no projetor e erros vinculados a campos. Aceite: tarefas centrais operáveis; capturas sozinhas não comprovam acessibilidade.
29. **Regressão da versão final — A/M.** Rodar testes pertinentes e navegador após integração; cobrir candidato, mentor, versões, conflitos e privacidade. Aceite: registro atual, Docker explicitamente separado; não reciclar resultados históricos como nova execução.
30. **Backup/restauração antes do ensaio — A/P-M.** Reutilizar `scripts/backup_database.py`, ensaiar restauração em outro arquivo e preservar chave. Aceite: cópia abre e mantém dados esperados sem substituir a base ativa.
31. **Contingência da apresentação — A/P-M.** Gravação curta, capturas e pontos de retomada da versão final; duas sessões de navegador para candidato/equipe. Aceite: demonstração pode continuar sem servidor/internet, identificando claramente o que é gravado.
32. **Teste com colegas e ensaio cronometrado — A/M.** Duas ou três pessoas tentam localizar vaga, retomar candidatura e entender feedback; registrar obstáculos. Aceite: corrigir bloqueios e ensaiar no equipamento de apresentação. Não equivale a validação de mercado.

## Sequência até 19/11

- **12/11:** fechar direção visual e escopo; itens 1–4 e 11–12 como primeira entrega visual; preparar base separada e execução inequívoca (25–26).
- **13/11:** integrar composição, recortes/otimização e navegação; conferir 390/768/1440 e projetor se disponível.
- **14/11:** login/retorno, próxima ação e cards; escolher melhorias B de maior retorno conforme avanço.
- **15/11:** ficha avaliadora, pendências úteis e conteúdo sintético; testar percurso completo sem Docker.
- **16/11:** teste com colegas, correções, acessibilidade e contingência.
- **17/11:** encerrar adição de funcionalidades; revisão integrada, regressão e backup/restauração.
- **18/11:** ensaio no equipamento, verificar projeção e material de reserva; apenas correções bloqueantes.
- **19/11:** confirmar versão/base/porta, preparar sessões e apresentar; evitar atualização de dependências ou alterações grandes.

Esse calendário é uma ordem proposta, não estimativa de capacidade garantida. Se houver atraso, cortar itens B/C, preservar fluxo principal, privacidade e ensaio. Docker depende de espaço disponível e instalação própria, não bloqueia o roteiro principal.

## Imagem conceitual gerada

Ferramenta integrada image_gen; proposta, não alteração do produto. Imagem original em output/qa/propostas-19-nov/hero-investigacao-conceito.png (fora do Git). Deve receber recortes/otimização e inspeção quando integrada. Direção: ilustração editorial de investigação profissional, fundo ameixa escuro/violeta, registros conectados a perfil humano, pessoa analista, materiais discretos e espaço negativo, sem texto/logos/capuz/código binário decorativo. Prompt integral guardado junto à imagem.

## Fora do escopo recomendado antes da apresentação

Multiempresa, novos papéis completos, e-mail real/recuperação de acesso, publicação pública, chat/IA de avaliação automática, execução de código arbitrário e troca de stack. São decisões maiores que exigem regras, operação e testes próprios. A lista acima já oferece expansão e acabamento sem essas dependências.

## Referências e limites

Código: templates/home.html, base.html, opportunities.html, my_applications.html, login.html, register.html, admin.html; CSS local; app.py, recruitment.py. Contexto: claude.md, docs/EVOLUCAO-23-MELHORIAS.md, APRESENTACAO.md e AVALIACAO-FINAL.md. Capturas novas em output/qa/analise-home-desktop.png e analise-home-mobile.png na raiz original. Alterações deste trabalho: somente este relatório e artefatos locais de análise; nenhum template, regra de negócio ou banco alterado.
