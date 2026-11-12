> Registro histórico. Para o estado e os testes da versão de apresentação, consulte [ENTREGA-APRESENTACAO.md](ENTREGA-APRESENTACAO.md).

# Revisão da interface e recuperação de formulários

Data: 6 de novembro de 2026. Escopo: templates e recursos de interface existentes, sem mudança de identidade visual ou novas dependências.

## Análise e correções

| Achado | Consequência | Correção |
| --- | --- | --- |
| A seção de relatos foi inserida também no bloco de título do dossiê | Texto e marcação dos relatos apareciam no título da aba e podiam ser incluídos em histórico de navegação | Mantida a seção apenas no conteúdo do dossiê; título contém somente o nome |
| Bloqueio de envio existia apenas no formulário Docker | Repetição involuntária de ações e falta de feedback em outros formulários | Todos os POST passam por controle de envio em andamento; a autorização e idempotência continuam responsabilidade do servidor |
| Listeners independentes de confirmação e carregamento | Um formulário cancelado poderia ficar bloqueado se recebesse os dois comportamentos | Confirmação ocorre antes do bloqueio; listeners posteriores que cancelam são respeitados |
| Botão desabilitado podia voltar desabilitado pelo cache de navegação | Usuário ficava sem conseguir reenviar após Voltar | pageshow restaura controles, textos e aria-busy, incluindo bfcache |
| Busca alterava a lista sem informar contagem a leitores de tela | Feedback visual não era equivalente ao assistivo | Contagem de resultados em região status visualmente oculta; mantém busca sem acentos |
| Limites de senha do login e observações não coincidiam com o servidor | Interface permitia comprimentos inconsistentes | Login até 128 caracteres e observações até 4000, alinhados ao backend |
| Símbolos decorativos em confirmações e links | Dependência visual de glifos sem necessidade | Removidos checks e setas; conteúdo comunicado por texto |
| Tabela de ranking vazio sempre reservava seis colunas | Participante sem coluna de dossiê recebia estrutura inconsistente | colspan condicionado ao papel |

O formulário de pausa/reabertura agora envia o estado de destino explicitamente em `active`, para o backend aplicar a transição de forma idempotente. Os rótulos dos botões utilizados pela automação foram preservados.

## Validação executada

- `node --check static/app.js`: aprovado.
- Compilação de todos os templates com Jinja: aprovada.
- Verificação do bloco de título do dossiê: sem seção HTML ou texto de relatos.
- Varredura de templates: sem emojis nos intervalos pictográficos e sem os checks/setas decorativos removidos.
- Chrome real, DOM isolado: cancelamento mantém formulário disponível; envio bloqueia repetição; pageshow com persisted restaura botão e rótulo; filtro sem acento funciona; contagem acessível e estado vazio conferidos.
- `git diff --check`: aprovado, somente avisos de conversão de quebra de linha do ambiente.

Roteiros e evidências temporários ficam em `output/qa`, ignorados pelo Git. O teste DOM isolado não substitui a regressão integrada do produto; o gerente executará essa bateria com o backend atualizado. Nenhuma publicação foi realizada por esta frente.
