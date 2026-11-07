# Diagnóstico e verificação do Docker — 7 de novembro de 2026

## Escopo

Diagnóstico da falha de readiness HTTP observada após a abertura do Docker Desktop. Não foram alterados código, imagem, recursos de outros projetos, configuração do daemon ou WSL. Foi criado um único container de diagnóstico com nome próprio e etiqueta do projeto, usando as mesmas restrições da aplicação; a flag aleatória foi fornecida pelo ambiente sem aparecer em argumentos ou relatório.

## Evidências

- A imagem local já contém a rota /health. Não foi necessário reconstruí-la.
- O container iniciou como running, sem OOM ou erro de processo, e seu healthcheck passou a healthy.
- A rota /health retornou HTTP200 no host com urllib padrão e também sem proxy.
- A consulta HTTP interna do container também retornou200.
- A chamada real orchestrator.start devolveu uma porta local; stop e status confirmaram a remoção posterior.
- Todos os containers criados neste diagnóstico e no teste foram encerrados. Não houve limpeza global.

A falha de readiness não foi reproduzida após o engine responder e a inicialização estabilizar. O comportamento observado é compatível com indisponibilidade transitória durante a inicialização, mas o diagnóstico não estabelece uma causa permanente nem justifica alterar limites de segurança ou reconstruir a imagem. Tentativas anteriores com timeout/erro500 não devem ser registradas como aprovadas.

## Bateria real concluída

Comandos executados com RUN_DOCKER_TESTS=1 e DOCKER_CONTEXT=desktop-linux:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_orchestrator.py -v
```

Resultado: **17 testes aprovados, zero falhas e zero ignorados**, em27,838 segundos. A integração real criou duas instâncias, verificou portas e flags distintas, restrições de execução e encerramento independente. Não é teste de carga, isolamento absoluto ou homologação de exposição pública.
