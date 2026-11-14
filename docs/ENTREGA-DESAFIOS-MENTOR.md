# Criação de desafios pela mentoria e catálogo corporativo

## O que foi adicionado

**Área "Criar desafios" (mentoria)** em `/admin/challenges`, com link no menu administrativo.

- Criar desafio: título, área/categoria (sugestões ou texto livre), pontos (10 a 1000), trilha, público, briefing e resposta correta.
- Editar: a resposta em branco mantém a atual; preenchida, substitui (vale só para novas tentativas).
- Ativar/desativar: desafio inativo some para participantes (lista, página do desafio, laboratório, totais). A mentoria continua vendo e abrindo.
- Excluir: somente desafios criados pela mentoria, sem tentativas, instâncias ou relatos. Os demais devem ser desativados para preservar histórico e ranking.
- A resposta é guardada apenas como hash SHA-256 e nunca é exibida de novo. A comparação é exata (maiúsculas e acentos), então o briefing deve indicar o formato.
- Desafios com ambiente virtual podem ter texto, pontos e visibilidade editados, mas não a flag (ela é gerada por instância).
- Título único, sem diferenciar maiúsculas de minúsculas.

**Catálogo corporativo** (`catalog_corporate.py`): 21 desafios para colaboradores, fora de TI, semeados de forma idempotente por título (nunca alteram respostas ou tentativas existentes).
Áreas: atendimento ao cliente, vendas, recursos humanos, financeiro, jurídico e compliance, logística, qualidade, saúde e segurança do trabalho, marketing, liderança e gestão, dados e planilhas, segurança da informação para todos.

**Filtro de público** na página de desafios (Candidatos, Colaboradores). Desafios do público "Todos" aparecem em qualquer filtro.

## Banco de dados

`challenges` ganhou `active` (padrão 1), `audience` (padrão `Candidatos`), `created_by` e `updated_at`, via migração incremental em `init_db`. Nada é apagado.

## Limites e decisões

- Não há novo papel de usuário (a regra do projeto é não criar papéis automaticamente). "Público" é um rótulo e filtro; todo participante autenticado vê os desafios ativos.
- Desativar um desafio não remove pontos já ganhos no ranking, mas ele deixa de contar no total "concluídos/total".
- As respostas dos desafios corporativos usam o formato `CTF{...}` para reaproveitar a validação existente. Perguntas abertas ou com correção humana não são suportadas por este mecanismo.
- Esta entrega foi verificada com testes automatizados e uma conferência no navegador (desktop e 375 px) com banco temporário. Não houve teste com a equipe nem com colaboradores reais, e os enunciados do catálogo corporativo não passaram por revisão de especialistas de cada área (especialmente jurídico/RH/SST).

## Verificação

- `tests/test_challenge_admin.py`: 20 testes (permissões, CSRF, validação, duplicidade, ativo/inativo, edição, exclusão, XSS, hash, migração idempotente e recálculo independente das respostas numéricas).
- Suíte completa: 186 testes, 2 ignorados (Docker real).
