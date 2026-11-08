# Purple Talent

Plataforma local de desafios CTF, avaliação de participantes e oportunidades. Integra a base Python/Flask e SQLite entregue pela equipe ao novo visual fornecido nas imagens do Figma e nas referências HTML/CSS/JavaScript da equipe.

## Executar no Windows

Requisitos: Python 3.12 ou superior. Docker Desktop com engine Linux é necessário somente para o laboratório Intranet. O recrutamento e as avaliações simuladas funcionam sem Docker. Na pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Abra **http://127.0.0.1:5000**. Cadastre sua conta de participante. O banco `lab.db` é preservado entre execuções; não o apague para atualizar a aplicação. A chave de sessão é gerada em `.session-key`, ou pode ser fornecida por `SECRET_KEY` no ambiente.

O acesso demonstrativo de mentoria herdado da equipe é `mentor@cti.local` / `mentor123`, criado apenas quando o banco não tem usuários. Bancos existentes mantêm suas credenciais. Esse acesso é exclusivo para demonstração local; esta versão não deve ser publicada na internet.

## Fluxos disponíveis

- Cadastro, login, logout e edição de nome/equipe.
- Arenas com busca e filtro, desafios de treino, dicas quando disponíveis e validação de respostas.
- Intranet Docker individual com flag única, porta local, limite de instâncias e expiração de 60 minutos.
- Investigação final em laboratório Docker isolado: captura fictícia de servidor com registros de acesso, eventos e processos, sem dicas. Os dados mudam por instância; trata-se de treinamento, sem garantia antifraude para seleção real.
- Ranking calculado a partir de desafios resolvidos, sem duplicar pontos por reenvio.
- Painel de mentoria, avaliação de quatro competências e dossiê com histórico imprimível.
- Vagas públicas em `/opportunities`; gestão pela mentoria em `/admin` e `/jobs`.
- Editor em `/admin/jobs/new`: rascunho, edição, publicação, pausa/reabertura, encerramento definitivo, prazo e metadados. Prévia restrita e proteção de edição simultânea.
- Formulário específico por vaga, configurado em editor visual; rascunho, revisão e confirmação da candidatura.
- Confirmação vinculada às respostas exibidas; mudanças em outra aba exigem nova revisão. O candidato pode registrar desistência nas etapas elegíveis, sem apagar respostas ou histórico.
- O editor de perguntas detecta alterações simultâneas e preserva os campos digitados quando há conflito.
- Formulários persistidos em tabelas relacionais SQLite: versões, perguntas, opções e respostas; não são armazenados como documentos JSON.
- Versões das perguntas preservadas desde a abertura do formulário, retorno à vaga após cadastro/login e proteção contra submissão duplicada.
- Avaliação seletiva simulada em três etapas por candidatura, com evidências de investigação, correlação e resposta; variantes SOC e AppSec.
- Revisão humana, acompanhamento de etapa e feedback; notas internas não são apresentadas ao candidato.
- Rubrica interna por competência, justificativa e histórico de revisões por candidatura, sem alterar os pontos de treino.
- Busca, filtros por vaga/etapa e paginação das candidaturas da equipe, mantendo rascunhos privados.

O indicador legado de compatibilidade de uma vaga compara a pontuação conquistada com a pontuação mínima informada. É um indicador simples, não uma decisão automática de contratação ou uma certificação de competência.

O painel **Minha evolução** apresenta progresso por área, atividade recente e relatos de solução, consultáveis pela mentoria. O contexto completo para continuidade está em [claude.md](claude.md).

## Arquitetura atual

O navegador utiliza HTML/Jinja, CSS e JavaScript locais. Flask processa os formulários e acessa SQLite. O orquestrador usa a CLI Docker no host para criar os desafios. Os containers não recebem o banco nem o socket Docker. Não foram acrescentados frameworks, bancos ou serviços à base da equipe.

As fontes Plus Jakarta Sans, Inter e JetBrains Mono são servidas localmente, com suas licenças. As referências da Rafaela permanecem preservadas.

## Verificar

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
docker compose --profile manual config --quiet
$env:RUN_DOCKER_TESTS = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_orchestrator.py -v
Remove-Item Env:RUN_DOCKER_TESTS
```

Os testes da aplicação usam bancos temporários e mocks do Docker. O teste real é separado e exige o daemon ativo. O teste opcional de navegador está em `tests/browser.cjs`; usa Playwright apenas como ferramenta de QA, fora das dependências do produto. Seu servidor isolado é iniciado com `.\.venv\Scripts\python.exe tests/serve_browser.py`, na porta 5055, e grava evidências em `output/qa`.

## Operação e limites

O servidor Flask está vinculado ao loopback e com debug desligado. O processo da aplicação deve permanecer aberto para remover ambientes expirados; se fechado, a limpeza volta na próxima execução. Não é um serviço de produção nem um ambiente multiusuário remoto. A rede Docker reduz comunicação entre instâncias, mas não constitui sandbox de execução de código arbitrário.

### Conferir o fluxo novo sem Docker

```powershell
.\.venv\Scripts\python.exe tests/serve_recruitment.py
```

Abra **http://127.0.0.1:5056**. Esse servidor de demonstração cria duas vagas identificadas como DEMO QA em banco separado, `output/qa/recruitment-browser.db`; não utiliza o banco da equipe. Cadastre uma conta sintética para experimentar. O acesso de mentoria usa a credencial local demonstrativa descrita acima. Nenhum e-mail é enviado.

As avaliações seletivas são cenários textuais com revisão humana; não provisionam novos alvos Docker nem executam comandos. Pontuação de treino não é reaproveitada como nota da seleção. Nesta entrega, a mentoria continua responsável pelo recrutamento interno; perfis separados de administrador/recrutador e isolamento multiempresa ainda não foram implementados.

Para criar o alvo Intranet opcional: `docker compose --profile manual build web01`.

Detalhes de preparação e diagnóstico estão em [docs/DOCKER.md](docs/DOCKER.md). O histórico desta integração está em [docs/mudanca.md](docs/mudanca.md), e a matriz de resultados em [Plano de Testes de Software & GOT.docx](<docs/Plano de Testes de Software & GOT.docx>).

Não publique `lab.db`, `.session-key`, `.env`, dados de usuários ou evidências privadas. O repositório público contém somente código, documentação e recursos visuais; dados locais e segredos ficam ignorados.

Detalhes desta etapa e verificações: [Entrega de recrutamento](docs/ENTREGA-RECRUTAMENTO.md).

A gestão completa de vagas está documentada em [Entrega da gestão de vagas](docs/ENTREGA-GESTAO-VAGAS.md). Pausa e prazo bloqueiam novos envios sem apagar candidaturas; encerramento é definitivo. A avaliação de uma inscrição já enviada continua disponível após o encerramento da vaga.
