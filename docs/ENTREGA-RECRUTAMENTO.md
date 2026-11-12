> Registro histórico. Para o estado e os testes da versão de apresentação, consulte [ENTREGA-APRESENTACAO.md](ENTREGA-APRESENTACAO.md).

# Entrega local — recrutamento por evidências

Registro da primeira entrega de 06/11/2026. A gestão editorial posterior está em [ENTREGA-GESTAO-VAGAS.md](ENTREGA-GESTAO-VAGAS.md); consulte esse registro para o estado mais recente.

Esta etapa implementa vagas públicas, autenticação com retorno à vaga, perguntas específicas configuráveis, rascunho, revisão e confirmação, acompanhamento, painel da mentoria e avaliação textual simulada em três etapas por candidatura.

## Persistência e migração

Os formulários são relacionais no SQLite: job_form_versions, form_questions, form_options, application_answers. A versão apresentada é vinculada à pessoa/vaga por token assinado; versões antigas permanecem disponíveis para preservar o significado das respostas. Perguntas e respostas não são documentos JSON. A migração lê o formato JSON anterior somente para converter registros existentes e preserva o material legado sem novas escritas operacionais.

A avaliação utiliza selection_assessments, selection_stages e selection_responses. As três etapas possuem investigação, correlação e resposta no cenário SOC; reconhecimento autorizado, análise de risco e correção no cenário AppSec. São exercícios escritos, não novos alvos executáveis. Não pontuam o ranking de prática livre.

A administração atual é exercida pelo perfil mentor. Notas internas ficam separadas do feedback visível ao candidato. Mudanças de etapa têm histórico persistido. Candidaturas em rascunho não aparecem como inscrições recebidas. O editor é visual, com campos convencionais; não exige edição de JSON.

## Verificações executadas

- Suíte integrada: 85 testes Python; 84 aprovados e 1 teste de Docker real opcional ignorado.
- 11 cenários Playwright/Chrome aprovados: vagas públicas, criação de vaga/editor, retorno após cadastro/login, obrigatoriedade, rascunho, revisão/confirmação, três etapas, revisão da mentoria, sigilo de notas, permissões, formulários diferentes e responsividade390/1440.
- Migrações de formulário e avaliação antigos para tabelas relacionadas verificadas em bancos temporários, inclusive repetição sem duplicidade e integridade referencial de formulários.
- Concorrência de confirmação, token adulterado/contexto incorreto, URLs inválidas, preservação de versão e pausa da vaga cobertos por testes.
- Sintaxe Python/JavaScript verificada. Capturas da landing e administração em mobile inspecionadas. Evidências privadas ficam em output/qa, fora do repositório.

## Executar e conferir

Use README.md para iniciar a aplicação local. tests/serve_recruitment.py abre uma demonstração isolada em http://127.0.0.1:5056 com vagas fictícias e banco próprio. A suíte é executada com .venv/Scripts/python.exe tests/run_report.py. tests/browser_recruitment.cjs requer Playwright no ambiente de QA e esse servidor ativo; não é dependência do produto.

## Limites e próximos incrementos

Não há e-mail real, hospedagem pública, homologação de produção, isolamento multiempresa ou papéis separados de recrutador/admin. Gestão de vagas mantém publicação e pausa existentes; rascunho editorial completo, prazos, edição ampla e encerramento de vagas são incrementos posteriores. O processo não decide contratação automaticamente. SEO cobre metadados e noindex de áreas privadas; domínio/canonical/sitemap público dependem do futuro deploy.

O histórico de vagas, as respostas e os bancos locais não devem ser apagados para atualizar. Testar migração em cópia e guardar backup antes de aplicar a um banco real. Não há migração reversa automática; versões legadas preservadas não substituem backup. Nenhum banco real da equipe foi necessário para QA.

Publicação autorizada pelo usuário: somente Breno-J-Oliveira/salvamento. Nenhuma alteração enviada a purple-talent nesta etapa.
