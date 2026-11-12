# Integração visual e preparação para 19 de novembro

Entrega local em 12/11/2026, sobre o commit 9ee1201 de Breno-J-Oliveira/salvamento. O usuário autorizou publicar esta integração em Breno-J-Oliveira/salvamento. A publicação do código não instala Docker nem implanta um serviço público. O relatório de análise é ANALISE-ATE-19-NOVEMBRO.md; esta entrega registra o que foi efetivamente integrado.

## Resultado

- Landing editorial com mensagem mais curta, duas artes originais, capturas reais do produto com dados fictícios, jornada, vagas realmente abertas, explicação da avaliação humana e FAQ reorganizado.
- Navegação pública por intenção, menu móvel progressivo operável por teclado, Escape e alternativa sem JavaScript; Entrar visível e cadastro acessível pelo menu em telas pequenas.
- Rodapé com atalhos reais e contexto acadêmico, conjunto vetorial local de ícones e refinamento de tipografia/espacamento sem trocar fontes ou paleta.
- Login/cadastro voltados à candidatura, controle de visibilidade de senha e prioridade do formulário no celular.
- Login geral de participante leva às candidaturas; retorno seguro à vaga e destino administrativo permanecem.
- Vagas com resumo menor, hierarquia e ações alinhadas; detalhe informa preparação e quantidade de perguntas da versão atual, sem criar formulário no GET público nem mostrar gabarito.
- Candidatura com próxima ação por estado. Avaliação entregue aguarda a equipe, em vez de convidar a preenchê-la novamente. Rascunho fechado mantém consulta pelo extrato.
- Ficha administrativa com âncoras para respostas, avaliação, competências, parecer e histórico; nota interna e feedback continuam separados.
- Painel com filas reais e filtros de avaliação entregue sem primeiro parecer versus avaliação ainda não entregue, respeitando etapas e paginação.
- Launcher local resolve a pasta correta, identifica commit/porta/base e recusa porta ocupada sem encerrar outro processo.
- Preparador explícito de demonstração cria somente arquivo novo, com duas vagas, rascunho retomável e candidatura com avaliação/rubrica/feedback fictícios. Não popula o banco da equipe.
- Roteiro de 7–10 minutos sem Docker; gravação opcional por papel e PDF sintético para contingência.

## Execução

Nesta máquina a versão atual está em .runtime/salvamento-atual e usa a .venv da raiz original. O atalho INICIAR-PURPLE-TALENT.ps1 na raiz original aponta para este checkout. Na raiz deste checkout, scripts/run_local.ps1 funciona diretamente e procura a .venv local ou ancestral.

```powershell
.\scripts\run_local.ps1 -Port 5000
.\scripts\run_local.ps1 -Demo -Port 5057
```

5000 usa o banco local desta cópia; 5057 usa output/demo/presentation.demo.db, separado e fictício. Não inicie novamente numa porta já ocupada. A cópia anterior e seu banco na raiz original permanecem preservados; não executar app.py daquela raiz esperando a versão nova.

## Verificação

Registros da execução ficam em output/qa, ignorados pelo Git. Os números finais e comandos são resumidos também no início de claude.md. A suíte Python usa bases temporárias; os roteiros de navegador usam exclusivamente bases de QA/demo.

- tests/run_report.py: 168 testes Python, 166 aprovados e 2 reais Docker ignorados por indisponibilidade. Resultado final após as alterações de backend e templates; logs e JSON em output/qa.
- tests/browser_presentation.cjs: 15 cenários do novo percurso; exige PRESENTATION_BASE_URL explícita e recusa porta 5000. Altera a base fictícia: criar um arquivo novo antes de cada execução integral.
- tests/browser_recruitment.cjs: 18 cenários aprovados de regressão do recrutamento/editor em servidor QA 5056.
- tests/browser_vacancies.cjs: 10 cenários aprovados de regressão editorial. Duas expectativas foram atualizadas para o comportamento novo: destino após login e consulta de rascunho pausado sem CTA de continuação.
- Inspeção de capturas desktop/mobile da landing, autenticação e administração; teste de reflow equivalente a 200% com viewport reduzido. Isso não substitui teste completo com leitor de tela ou inspeção no projetor real.
- Contrastes calculados entre pares principais: texto/fundo 16,14:1; secundário/superfície 8,14:1; texto do botão/violeta 4,73:1; link/fundo 9,19:1. São medições desses pares, não uma declaração de conformidade de toda a aplicação.
- Backup da base local copiado e restaurado em novos arquivos de QA; integrity_check e contagens de users/jobs/applications/attempts preservadas, sem substituir a base ativa.
- Launcher recusou porta ocupada conforme esperado. JavaScript e templates passaram pelas verificações de sintaxe pertinentes.

## Contingência

tests/record_demo.cjs grava somente depois de autenticar, sem salvar cookies/sessões em disco. Usa dados fictícios e cria candidato.webm, equipe.webm e extrato-demonstracao.pdf em output/qa/presentation/contingencia. Os vídeos são capturas automatizadas sem narração: material de reserva, não execução ao vivo nem substituto de um ensaio humano.

## Limites e próximos passos

Não é promessa de perfeição. Docker não foi instalado/testado; laboratório executável permanece opcional. Não houve teste com colegas, leitor de tela ou projetor. Esses ensaios devem ocorrer antes de 19/11. Multiempresa, novos papéis, e-mail real, hospedagem pública, máquina de transições mais restrita e novos campos estruturados de vaga continuam fora desta entrega; foram classificados como trabalho posterior no planejamento. As confirmações definitivas existentes foram preservadas, sem um novo sistema de modais.

As mudanças não exigem migração destrutiva, troca de banco ou novo framework. Formulários e avaliações continuam relacionais e versionados. Nenhuma pontuação de treino decide a seleção e nenhuma nota interna é compartilhada automaticamente com candidatos.
