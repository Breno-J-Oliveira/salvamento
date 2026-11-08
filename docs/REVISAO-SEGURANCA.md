# Revisão de segurança — aplicação local

Revisão dirigida aos fluxos de autenticação, formulários, permissões e laboratórios. Não substitui auditoria independente nem homologação para acesso público.

## Achado corrigido

- **SEC-01 — limite de tentativas de autenticação contornável por sessão existente.** O limitador usava o identificador da sessão quando havia um usuário autenticado, trocando a chave antes associada ao endereço de origem. Uma sessão podia assim iniciar outra sequência de tentativas. Login e cadastro agora usam o endereço de origem mesmo em sessão autenticada; as demais ações mantêm o limite por usuário. Um teste reproduziu a falha antes da correção e verifica a resposta 429 após o limite. Referências: `app.py:50`, `tests/test_app.py:201`.

## Pendências antes de uso público

- **SEC-02 — limitação por processo.** Os contadores ficam na memória da aplicação e não coordenam processos ou máquinas (`app.py:28`). A política para proxy e o armazenamento compartilhado devem ser definidos e testados antes de escalar a aplicação.
- **SEC-03 — acesso demonstrativo.** O banco inicial pode criar uma conta de mentoria com credenciais conhecidas para uso local (`app.py:152`). Ela não é apropriada para exposição pública; o processo de provisionamento e troca de credenciais deve ser definido antes de operar com usuários reais.
- **SEC-04 — revogação de sessão.** O cookie de sessão assinado não dispõe, por si só, de revogação imediata de cópias já emitidas. Uma solução de sessões revogáveis precisa ser planejada para operação pública.
- **SEC-05 — operação e dados.** São necessários ensaios de backup e restauração, política de retenção, controle de acesso operacional e revisão de privacidade antes de dados reais. O servidor local de desenvolvimento (`app.py:610`) e os laboratórios não foram homologados como serviço público.

O controle CSRF, verificações de papel, parametrização de consultas e o isolamento configurado dos laboratórios permanecem relevantes, mas testes pontuais não comprovam ausência de falhas.
