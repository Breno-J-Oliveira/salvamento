# Ambientes virtuais Docker

O projeto usa Python e Flask no computador local e Docker para executar os desafios isolados. O SQLite permanece com a aplicação; os containers dos desafios não recebem o arquivo de banco, código da plataforma, volumes do host ou socket Docker. Não é necessário instalar outro framework ou banco.

## Preparar

1. Abra Docker Desktop e aguarde o engine Linux ficar disponível.
2. Na raiz do projeto, execute:

```powershell
docker info
docker compose --profile manual build web01
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Consulte o README principal para a configuração inicial de acesso. Não publique senhas, chaves de sessão ou o banco local. A aplicação fica em `http://127.0.0.1:5000`.

## Utilizar um desafio

Entre como participante, abra **Intranet esquecida** e clique em **Iniciar ambiente**. O orquestrador verifica a imagem permitida e a rede, cria uma instância individual com uma flag aleatória e só libera o endereço depois que a verificação HTTP de disponibilidade responder. O Docker escolhe uma porta livre; o endereço aparece na tela. A flag não é compartilhada entre participantes.

Use **Encerrar ambiente** ao terminar. A plataforma controla o prazo de expiração e o limite de instâncias. A mentoria dispõe da tela de ambientes para acompanhar e encerrar instâncias. Uma falha do Docker deve ser apresentada como falha, sem registrar um encerramento inexistente.

As instâncias usam portas vinculadas exclusivamente a `127.0.0.1`, usuário sem privilégios, sistema de arquivos somente leitura, memória de 128 MiB, limite de CPU de 0,5 e até 64 processos. O diretório temporário tem limite de 16 MiB. Todas as capabilities Linux são removidas e a elevação de privilégios fica desabilitada.

## Diagnóstico manual opcional

```powershell
docker compose --profile manual up -d web01
docker compose --profile manual ps
docker compose --profile manual logs --tail 30 web01
docker compose --profile manual down
```

Esse laboratório fica em `http://127.0.0.1:5001` e usa uma flag de diagnóstico sem pontuação na aplicação. Ele não substitui a instância criada pela tela. Não execute comandos de remoção global de containers ou volumes.

## Verificação

```powershell
docker compose --profile manual config --quiet
python -m unittest discover -s tests -p test_orchestrator.py -v
$env:RUN_DOCKER_TESTS = '1'
python -m unittest discover -s tests -p test_orchestrator.py -v
Remove-Item Env:RUN_DOCKER_TESTS
```

Os testes comuns validam nomes e imagens permitidos, tratamento de falhas, portas locais e argumentos de segurança sem depender do daemon. O teste habilitado por `RUN_DOCKER_TESTS` inicia duas instâncias reais, verifica flags distintas, configurações de recursos e encerramento independente, e remove somente as instâncias que criou. Sem essa variável, o teste real aparece explicitamente como ignorado.

## Limites e recuperação

Esta configuração destina-se ao uso local. Um navegador em outra máquina não acessará os endereços `127.0.0.1` deste computador. Não publique as portas na internet nem transforme o desafio em executor de código arbitrário.

A rede bridge dedicada desabilita a comunicação direta entre containers (`enable_icc=false`). Isso não equivale a bloquear toda comunicação de saída ou acesso ao host, nem a um isolamento absoluto. O desafio atual oferece apenas descoberta de arquivo por HTTP, sem execução de comandos ou upload.

O controle Docker roda no host. Não montamos o socket Docker dentro de um serviço web ou do desafio. Se o Docker estiver desligado, abra o Desktop e tente novamente. Se a rede `cti-lab-net` já existir com configuração incompatível, o orquestrador recusa iniciar a instância; investigue os containers vinculados antes de alterar essa rede. Nunca remova redes ou containers de outros projetos para corrigir o laboratório.
