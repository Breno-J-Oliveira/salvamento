# Equipes, modo de foco nos desafios e correção de cards

## Equipes Red Team e Blue Team (`/teams`)

- Cada equipe tem um lado (Red Team ou Blue Team) e **até 4 pessoas**. Uma pessoa participa de **uma** equipe por vez.
- O participante cria uma equipe (nome de 3 a 40 caracteres, único sem diferenciar maiúsculas), entra em uma com vaga livre ou sai. Equipe que fica vazia é removida.
- O limite de 4 é verificado dentro de uma transação, então entradas simultâneas não passam do limite (há teste com 8 entradas ao mesmo tempo).
- A pontuação da equipe conta cada desafio uma vez, mesmo que mais de um integrante o resolva. A pontuação individual e o ranking individual não mudam.
- A mentoria vê todas as equipes, remove integrantes e desfaz equipes. Mentoria não entra em equipes.
- Ao entrar ou sair, o campo `users.team` (usado no painel de avaliação) é atualizado para o nome da equipe ou "Sem equipe".
- Tabelas novas: `teams` e `team_members` (migração incremental, nada é apagado).
- Menu: "Aprender > Equipes" para participantes; "Equipes" na barra da mentoria.

## Desafios de equipe: equipe obrigatória

- Desafios das trilhas **Red Team** e **Blue Team** exigem que o participante esteja em uma equipe **do mesmo lado**. Sem isso, a página do desafio mostra só o aviso "Desafio em equipe" com atalho para `/teams`: não exibe o briefing, não aceita flag (resposta 403), não inicia o ambiente virtual e não inicia a contagem de tempo.
- **Aquecimento** e **Corporativo** continuam livres. A mentoria não é afetada.
- Vale também para desafios Red/Blue criados pela mentoria (o formulário avisa).
- A lista de desafios mostra "Requer equipe Red/Blue Team" nos bloqueados e um aviso sobre a situação do participante.
- Sair da equipe bloqueia de novo; tentativas e pontos já feitos continuam registrados.
- A regra exige **pertencer** a uma equipe, não que ela esteja completa (4 de 4). Exigir equipe completa é uma mudança pequena, se desejada.
- Sem teste com Docker real: o bloqueio de iniciar ambiente foi verificado com o orquestrador simulado.

## Modo de foco no desafio

Enquanto o participante resolve um desafio ainda não concluído, a página mostra o aviso "Modo de foco ativo" e:

- pede confirmação do navegador ao tentar fechar, recarregar ou voltar;
- registra uma **ocorrência** ao trocar de aba, minimizar, sair da janela, sair da tela cheia ou tentar sair da página;
- mostra na hora o contador e o horário da ocorrência;
- oferece o botão "Entrar em tela cheia" (opcional, exige clique por regra do navegador).

Exceções: enviar a flag e iniciar/encerrar o ambiente recarregam a página sem gerar ocorrência, e abrir o laboratório em outra aba é uma saída autorizada. O modo não vale para a mentoria nem para desafios já concluídos.

A mentoria consulta as ocorrências em **Ocorrências** (`/admin/occurrences`, com resumo por participante e as últimas 200) e no dossiê de cada participante. Eventos em sequência dentro de 2 segundos contam como um, e há limite de 200 por participante e desafio.

### Limites importantes

- **O navegador não permite impedir que alguém troque de aba, use outro aparelho ou feche a janela.** O recurso avisa, pede confirmação e registra; não é antifraude.
- Ocorrência é indicador, não prova: queda de internet, notificação do sistema ou consulta legítima também podem gerar registro. Use para conversar com a pessoa.
- O aviso nativo "Sair do site?" só aparece depois que a pessoa interagiu com a página (regra do Chrome); o registro da ocorrência acontece de qualquer forma.
- O fluxo com o laboratório Docker (abrir o ambiente em outra aba) foi tratado no código, mas **não foi testado com Docker real** nesta etapa.
- Tabela nova: `occurrences`.

## Correção de cards

- Caixas internas dos cards de candidatura ("Continue sua inscrição", "Situação desta candidatura", feedback, histórico) estavam coladas porque `.opportunity-card p { margin: 0 }` zerava o espaçamento. Agora têm espaçamento próprio.
- Lista de desafios em larguras médias e pequenas: o botão ficava esticado em larguras diferentes e a pontuação solta. Agora cada card tem três faixas alinhadas (descrição, etiqueta e pontos, botão em largura total).
- Barra de progresso de "Minha evolução" aparecia cheia mesmo em 0%; agora o trilho é escuro.
- Texto longo quebra dentro dos cards; ações dos cards de vaga e filtro de candidaturas têm espaçamento e alinhamento consistentes.
- Tudo em `static/layout-fixes.css`, carregado por último.

## Verificação

- `tests/test_teams_occurrences.py`: 18 testes (permissões, CSRF, limite de 4 com concorrência, uma equipe por pessoa, saída e remoção, pontuação sem duplicar, XSS, ocorrências, deduplicação, limite, visão da mentoria).
- Suíte completa: 204 testes, 2 ignorados (Docker real).
- Navegador, com base de demonstração temporária: tela de equipes, modo de foco (eventos de troca de aba simulados e gravação conferida no banco), cards em 375 px sem rolagem horizontal.
- **Não executado:** os roteiros Playwright em `tests/*.cjs` e leitor de tela. Os desafios ganharam um banner novo, então esses roteiros podem precisar de ajuste.
- Não houve teste com pessoas reais nem troca real de aba por um usuário.
