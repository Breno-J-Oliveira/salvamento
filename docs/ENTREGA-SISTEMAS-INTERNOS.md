# Gestão de desafios e avaliações internas

Entrega incremental de 12/11/2026, após o polimento de apresentação. Autorização do usuário: desenvolver os novos sistemas e publicar ao final somente em Breno-J-Oliveira/salvamento. Flask, SQLite, Jinja e assets locais permanecem; não há instalação ou exposição pública de serviços.

## Gestão de desafios

A mentoria acessa `/admin/challenges`. Pode criar desafios textuais, preparar rascunhos, publicar e pausar. Título, categoria, área, pontuação, briefing, dica e resposta são validados no servidor. A resposta é persistida somente em hash; nunca volta preenchida na edição ou no HTML. Uma resposta vazia na edição preserva o hash atual. Erros preservam os textos, exigindo digitar a resposta novamente se necessário.

Rascunhos e pausados não aparecem no catálogo nem recebem tentativas por URL direta. O estado é revalidado dentro da transação de envio. Pontos, área e resposta congelam após qualquer tentativa para preservar o significado do histórico e do ranking. Uma dinâmica diferente exige outro desafio. Títulos dos desafios herdados ficam preservados para o seed não duplicá-los; novos itens têm título editável. Briefings continuam editáveis com aviso de cuidado.

Edição simultânea retorna HTTP 409 e mantém os campos digitados. `challenge_history` registra autor, estado e revisão sem guardar respostas. A configuração dos laboratórios existentes permanece somente leitura neste editor: ele não recebe imagem Docker arbitrária, comando, arquivo ou upload executável. A dica cadastrada é conteúdo de apoio editorial; não foi reintroduzido botão de solução na interface de treino.

## Avaliações corporativas internas

Fluxo: `/admin/assessments` → preparar contexto e três perguntas → atribuir a uma conta existente → funcionário acessa `/my-assessments` → salva rascunho → envia definitivamente → mentor registra revisão por competência → funcionário consulta feedback.

Há exemplos editáveis SOC e de acesso/mensagem suspeita, com dados sintéticos e hipóteses a investigar. Escolher exemplo apenas preenche o editor; nada é salvo ou atribuído sem ação da equipe. As perguntas são discursivas; não executam comandos e não testam infraestrutura real de uma empresa.

As definições, perguntas, atribuições, cópias recebidas e revisões ficam em tabelas relacionais. Cada atribuição copia título, contexto, perguntas, versão e prazo. Edições futuras da definição não reescrevem o material recebido. Para um novo ciclo com a mesma pessoa, crie uma nova avaliação; uma definição só é atribuída uma vez à mesma conta.

Prazo opcional considera o fim do dia em Brasília e bloqueia novas respostas após expirar. Rascunhos aceitam respostas incompletas; o envio exige três análises de 30–6000 caracteres. Após envio, respostas ficam definitivas. Notas 0–5 para investigação, evidências, decisões e comunicação, justificativa e notas internas são restritas à mentoria; apenas o feedback vai ao funcionário. Não há pontuação CTF, promoção de conta, aprovação automática ou garantia de competência.

Revisões otimistas cobrem editor, respostas e pareceres. A revisão independente reproduziu revisão numérica de 5000 dígitos causando erro; a entrada passou a ser limitada antes da conversão e tem regressão nos três escritores. Testes também cobrem troca de IDs, snapshots, prazos e privacidade.

## Docker: o que foi realmente conferido

`/admin/laboratory-status` permite à mentoria consultar a disponibilidade. GET não consulta daemon automaticamente. O POST exige CSRF, é somente leitura e diferencia CLI ausente, engine indisponível e engine respondendo. A consulta não constrói imagens nem cria/remove containers, e não mostra stderr bruto.

Neste computador sem CLI Docker, foram exercitados de verdade o diagnóstico e o POST de início do laboratório em base temporária, sem mock do Docker nesse caso. O site respondeu com aviso, permaneceu navegável e não gravou instância inexistente. Também há testes controlados para falha e sucesso da consulta ao engine.

Isso comprova o tratamento da indisponibilidade. **Não comprova criação, rede, healthcheck, isolamento ou execução real de containers.** Os testes reais continuam opcionais e precisam de um computador com engine instalado. Não há modo fictício que informe container ativo sem ele existir. Consulte também docs/DOCKER.md.

## Revisão visual

As artes geradas deixaram de ser usadas na landing e autenticação. Foram substituídas por elementos HTML/CSS: registros ilustrativos, sequência de investigação e checklist. O exemplo é identificado como sintético, legível e responsivo. Capturas reais do produto com dados fictícios permanecem. Os arquivos antigos foram preservados por histórico, sem referências nas três telas.

## Verificação e operação

- `tests/run_report.py`: 187 testes Python, 185 aprovados e 2 reais Docker ignorados. Suíte integral registrada em output/qa/systems-unit-final.log e output/qa/unit-results.json; os testes reais Docker são separados dos testes de indisponibilidade.
- `tests/browser_systems.cjs`: 10 cenários novos Chrome aprovados em base fictícia descartável, incluindo layouts de 390/768/1440 px, permissões e ausência de erros JS.
- `tests/browser_recruitment.cjs`: 18 cenários aprovados de regressão do recrutamento existente em servidor QA independente.
- Bancos local e demonstrativo receberam backup SQLite verificado antes da atualização; as bases de testes permanecem isoladas e ignoradas pelo Git.

As migrações são incrementais e idempotentes, preservando colunas/tabelas e os IDs antigos. Como o schema avança, não reverter binário por cima da base sem conferir compatibilidade; restaurar uma cópia deve usar destino novo com scripts/backup_database.py. Não apagar banco/chave para atualizar.

O servidor local permanece em 5000 e a demonstração em 5057. A equipe precisa criar/atribuir suas avaliações explicitamente; nenhum registro corporativo foi inserido automaticamente no banco real. A apresentação pode mostrar todo esse fluxo sem Docker. Nenhum e-mail é enviado.

## Limites

É gestão interna por mentoria, sem isolamento entre organizações, provisionamento de funcionários ou políticas empresariais de RH. A conta existente com papel participante também pode receber avaliação interna, sem mudança de privilégios. O painel corporativo ainda não tem paginação, cancelamento de atribuição ou relatórios estatísticos empresariais. Testes com colegas, leitor de tela e aceite da equipe continuam necessários; não declarar homologação de produção ou funcionamento Docker real.
