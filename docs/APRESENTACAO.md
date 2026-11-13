# Roteiro de demonstração — Purple Talent

## Antes de apresentar o laboratório acompanhado

Inicie a primeira VM com antecedência e confira a indicação de ambiente conectado em `/remote-labs`. Para demonstrar a seleção, abra dois perfis de navegador, um de candidato e outro de mentor. O candidato pode sair da página e usar **Retomar investigação**; o mentor acompanha a mesma sessão na sua conta. Encerre a investigação quando terminar de mostrar os resultados. Se outro candidato for participar, deixe a rodada local em execução e aguarde o próximo ambiente aparecer. [Comandos da rodada](LABORATORIOS-REMOTOS.md#rodada-local-de-candidatos)

## Preparação e versão correta

Na pasta da versão escolhida, execute no PowerShell:

```powershell
.\scripts\run_local.ps1 -Demo -Port 5057
```

O launcher mostra pasta, commit, Python, banco e endereço antes de iniciar o servidor. Resolve a `.venv` local ou de uma pasta ancestral, sempre executa o `app.py` ao lado deste roteiro e usa somente `127.0.0.1`. Se a porta estiver ocupada, recusa iniciar e não encerra processos alheios; escolha outra porta. A versão pode ter alterações locais além do commit mostrado.

O modo `-Demo` é explícito: na primeira execução cria `output/demo/presentation.demo.db`, sem ler/copiar o banco da equipe. Nas seguintes, retoma esse arquivo somente se encontrar seu marcador de demonstração. Não restaura automaticamente o estado inicial: alterações feitas durante o ensaio permanecem. A sessão da demo é renovada ao reiniciar; faça login novamente. Nenhum e-mail é enviado.

Para começar outro ensaio do zero, use um nome novo, preservando o anterior:

```powershell
.\scripts\run_local.ps1 -Demo -Database output/demo/ensaio-02.demo.db -Port 5058
```

Preparação sem abrir servidor, se necessário:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_demo.py output/demo/ensaio-03.demo.db
```

Se a `.venv` estiver numa pasta ancestral, use o caminho de Python exibido pelo launcher. O preparador recusa destinos existentes, links simbólicos e arquivos chamados `lab.db`. Nunca use o banco da equipe como fixture nem renomeie um banco real para contornar a proteção.

O modo local normal permanece disponível: `.\scripts\run_local.ps1 -Port 5000` usa `lab.db` desta versão, ou `-Database` escolhe explicitamente outra base. Confira a pasta e o caminho completo antes de continuar. Nenhum script apaga ou substitui dados existentes, e nenhum instala dependências automaticamente.

## Contas e pontos de retomada

Todos os registros da demo são fictícios. Não há processo real de contratação.

- Candidato preparado: `candidato@demo.invalid`, senha local de demonstração `demonstracao123`. Há uma candidatura SOC na etapa entrevista, com respostas, avaliação, rubrica e feedback; e um rascunho AppSec para continuar.
- Equipe: acesso demonstrativo descrito no [README](../README.md), criado somente nesta nova base. Se `MENTOR_PASSWORD` estiver definido ao preparar a demo, esse valor é respeitado; não altere credenciais reais para ensaiar.
- Duas vagas publicadas: “DEMO — Analista SOC Júnior” e “DEMO — Estágio em AppSec”, com prazo de 30 dias a partir da preparação. Para apresentações posteriores, prepare outro arquivo novo.
- Para mostrar inscrição desde o início, cadastre uma segunda pessoa fictícia na demo. A conta preparada já tem inscrição nas duas vagas; não tente duplicá-las.

Use janelas separadas para candidato e equipe, sendo uma privativa ou outro perfil de navegador para evitar compartilhar a sessão. Não coloque senhas em slides, capturas ou gravações da apresentação.

## Percurso principal sem Docker — 7 a 10 minutos

1. **Proposta, 1 minuto.** Abra a landing. Explique o problema: currículos e pontuação isolada não mostram como alguém investiga. O produto organiza respostas, evidências e revisão humana por vaga.
2. **Oportunidade, 1 minuto.** Mostre busca e modalidade nas vagas fictícias. Abra AppSec e explique critérios e prazo. Não afirme parceria, contratação real ou recursos de produção.
3. **Candidatura, 2 minutos.** Entre como candidato preparado, abra “Minhas candidaturas” e continue o rascunho AppSec. Complete a resposta de escolha única, salve e recarregue. Revise e confirme o envio. Os dados ficam persistidos, sem depender de Docker.
4. **Avaliação, 1 minuto.** Abra a avaliação da AppSec recém-enviada para mostrar artefatos e etapas. Não é necessário preencher os três pareceres ao vivo: cada etapa é definitiva. Explique a separação entre treino e seleção.
5. **Revisão humana, 2 minutos.** Na janela da equipe, filtre a candidatura SOC já preparada. Mostre as respostas, evidências, rubrica e justificativa existentes. Compare a nota interna com o feedback compartilhável. Registre uma pequena atualização de feedback apenas na base demo, se houver tempo.
6. **Retorno e encerramento, 1 minuto.** Na janela do candidato, abra o feedback SOC e o extrato imprimível. Conclua mostrando como a informação acompanha o processo, sem classificação ou contratação automática.

Se houver mais tempo, mostre o editor: duplicação/reordenação de perguntas, prévia e gabarito opcional privado. Crie outro rascunho de vaga para isso; as inscrições existentes mantêm suas versões. Demonstre desistência somente numa candidatura descartável, pois ela encerra a participação e mantém o histórico.

## Contingência e recuperação

- **Sem Docker:** o percurso principal permanece completo. A lista de laboratórios explica o contexto; não clique em “Iniciar ambiente” sem engine instalado e ativo. Nunca apresente gravação como execução ao vivo.
- **Sessão trocada:** retome login na janela correta; não altere papéis no banco. As respostas salvas continuam no arquivo demo.
- **Rascunho já enviado:** mostre o histórico e o extrato; para repetir o preenchimento, use outra pessoa fictícia ou prepare outro banco com nome novo antes da apresentação.
- **Etapa já finalizada:** mostre a evidência armazenada; não tente sobrescrever. A candidatura SOC preparada é o ponto de retomada do parecer e feedback.
- **Servidor indisponível:** confira endereço, porta, pasta/commit e base mostrados pelo launcher. Não mate outro processo para liberar a porta; use outra. Reexecute o mesmo comando para retomar os dados da demo.
- **Falha no computador:** prepare previamente uma gravação curta e capturas/PDF com dados sintéticos da versão final. Esses materiais são contingência a produzir no ensaio, não artefatos gerados por este roteiro.

Ensaie com cronômetro, a resolução do projetor e zoom de 125%. Antes do dia 19, confirme que os links e os dois logins funcionam. Um ensaio é bem-sucedido quando chega do formulário ao feedback sem editar SQLite, reiniciar a demonstração ou revelar notas internas na janela do candidato.

## Laboratórios opcionais e limites

Docker é uma extensão separada do percurso principal. Se houver espaço e engine Linux já preparado, construa as imagens conforme [DOCKER.md](DOCKER.md), abra a Intranet ou o console final e encerre somente o ambiente da própria demonstração. Não tente instalar Docker ou reconstruir imagens durante a apresentação.

O console representa captura fictícia, sem ataque à infraestrutura real. A aplicação continua local; operação pública exige hospedagem, HTTPS, equipe provisionada, política de dados, recuperação de acesso e validação operacional. Os testes registrados nos relatórios têm versões e datas específicas; não são garantia de invulnerabilidade, aceite empresarial ou nova homologação.

Para dados da equipe, preserve banco e chave. A ferramenta de [backup](../scripts/backup_database.py) cria cópia verificada em destino novo; ensaie restauração em outro arquivo antes de qualquer troca operacional. Não apague `lab.db` para corrigir inicialização.
