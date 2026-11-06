# Revisão de confiabilidade dos laboratórios Docker

Data: 6 de novembro de 2026. Escopo: orquestrador existente, sem novas funcionalidades, dependências, remoção de redes ou alterações de dados.

## Análise anterior à alteração

O orquestrador já restringia imagens, nomes e portas locais e verificava a etiqueta dos containers antes de encerrar. A revisão encontrou lacunas em respostas incompletas do Docker e na recuperação de falhas:

- A inspeção da rede assumia JSON válido e uma lista não vazia, permitindo exceções de implementação em vez de erro compreensível.
- A opção ICC era conferida, mas o driver bridge da rede não era validado.
- A porta retornada pelo Docker era convertida para inteiro sem validar o intervalo permitido.
- Se a inicialização falhasse e a limpeza também falhasse, a segunda exceção substituía a primeira, prejudicando o diagnóstico.
- Consultas e encerramento tinham prazos diferentes sem uma política explícita.
- Erros de permissão ou execução da CLI que não fossem ausência do executável não eram normalizados.

## Correções

Respostas de rede inválidas agora geram `DockerError`. Redes existentes são utilizadas somente quando têm driver bridge e ICC desabilitado. Não se exige etiqueta de uma rede legada válida e ela não é recriada automaticamente.

A porta deve estar entre 1 e 65535 e vinculada ao loopback. A recuperação de uma inicialização confirmada continua tentando encerrar a instância criada; quando essa limpeza falha, o erro inicial é preservado, recebe uma nota de diagnóstico e um aviso sem flags ou caminhos sensíveis é registrado.

Consultas de rede, imagem, estado e propriedade usam prazo de cinco segundos. Criação de rede e remoção usam vinte segundos. O build inicial continua permitindo até dez minutos e a espera de disponibilidade HTTP continua em trinta segundos. Assim, a primeira preparação pode permanecer demorada e o estado de carregamento da interface continua necessário.

Falhas de execução do sistema operacional são convertidas em mensagem pública segura. O contrato `start` retorna a porta, `status` retorna presença e `stop` permanece idempotente quando a instância está ausente; erros reais continuam propagados.

## Verificação executada

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_orchestrator.py -v
$env:RUN_DOCKER_TESTS='1'
$env:DOCKER_CONTEXT='desktop-linux'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_orchestrator.py -v
```

Primeira execução: 16 testes aprovados e uma integração real explicitamente ignorada. Segunda execução: **17 testes aprovados, zero ignorados**, em 24,211 segundos. A integração criou duas instâncias reais com portas e flags distintas, conferiu restrições, encerrou uma sem afetar a outra e removeu os recursos criados pelo teste.

Casos acrescentados: JSON malformado ou vazio, driver incompatível, rede legada válida, porta fora do intervalo, falha de limpeza preservando erro inicial, prazo de encerramento, timeout de readiness com recuperação e falha de execução sem vazamento.

## Limites que permanecem

Se o daemon não responder durante a limpeza, uma instância pode continuar em execução e exigir reconciliação operacional; a falha não é apresentada como sucesso. Um timeout da chamada `docker run` não comprova se o daemon chegou a criar o container. Não se executa limpeza indiscriminada nesse caso porque o nome poderia já existir e pertencer a uma operação anterior.

Estes testes não equivalem a certificação de isolamento, controle multiprocesso ou homologação para exposição pública. A arquitetura continua destinada ao laboratório local educativo.
