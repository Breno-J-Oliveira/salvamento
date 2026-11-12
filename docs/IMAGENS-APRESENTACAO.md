# Imagens e capturas da apresentação

> Histórico: na entrega dos sistemas internos, as artes geradas abaixo deixaram de ser usadas na landing e autenticação. Foram substituídas por elementos HTML/CSS. As capturas reais permanecem. Consulte ENTREGA-SISTEMAS-INTERNOS.md.

Produzidas em 12/11/2026. As duas ilustrações foram criadas com a ferramenta integrada image_gen; os arquivos WebP finais são recursos locais da aplicação. Não dependem de CDN, API ou serviço de geração em tempo de execução. Os SVGs originais foram preservados. Os ícones novos são vetores locais determinísticos em static/icons.svg.

## Arquivos integrados

- static/images/investigation-hero.webp: ilustração principal, 1200×800, aproximadamente 44 KB.
- static/images/investigation-hero-mobile.webp: exportação para celular, 720×480, aproximadamente 20 KB.
- static/images/investigation-auth.webp: arte de autenticação, 720×900, aproximadamente 31 KB. A composição da interface faz o enquadramento; no celular a imagem decorativa fica oculta para priorizar o formulário.
- static/images/product-candidate.webp e product-review.webp: capturas reais da interface com dados fictícios, exportadas em 1200×800. Nenhuma delas é uma tela gerada por IA.

As capturas usam exclusivamente a base criada por scripts/prepare_demo.py, com Alex Demo e empresa explicitamente fictícia. A imagem administrativa contém exemplo sintético de nota interna para ilustrar a separação do feedback; não contém dados de seleção real. Não substituir por captura de banco da equipe. Atualizar as capturas quando o layout ou as ações mostradas mudarem.

As legendas distinguem ilustração conceitual e captura com dados fictícios. Texto essencial continua em HTML, com alternativas nas imagens, dimensões explícitas e carregamento adiado das capturas abaixo da primeira seção. As artes não sugerem parceria, contratação, ataque ao vivo ou aprovação automática.

## Prompt da arte principal

Create one polished editorial illustration concept for Purple Talent, a Brazilian cybersecurity student recruitment platform. Landscape 3:2, no text, no letters, no logos. Professional sophisticated 3D mixed with precise editorial illustration, dark plum background (#0e0c17), restrained violet (#a855f7), muted blue and warm pale highlights. Central visual metaphor: evidence becomes a human hiring decision. An elegant analyst desk seen in three-quarter perspective, a monitor with abstract correlating event lines and small evidence nodes (no legible UI), translucent artifact sheets arranged in a clear analytical sequence, a violet connecting thread ending in a simple human profile tile. Thoughtful calm human analyst represented subtly at right, no hoodies, no masks, no padlocks, no binary rain, no cyberpunk neon. Keep left quarter relatively quiet for future composition, main artwork middle/right, clear silhouette at small size, controlled light, tactile matte materials, premium product editorial art, plenty of negative space. This is concept artwork for review, not screenshot or claims of a real SOC. No typography.

## Prompt da arte de autenticação

Original editorial artwork for Purple Talent cybersecurity recruitment platform, companion to a calm premium dark plum and violet analyst desk illustration. Vertical 4:5 composition. A thoughtfully composed matte sculptural still life: organized evidence folders, translucent sheets with abstract interconnected event nodes, a small upright human profile silhouette card and subtle desk lamp. No text, no letters, no digits, no logos. Professional, quiet, inviting, dark plum #0e0c17, violet #a855f7, pale lavender and restrained warm light. Tactile 3D editorial illustration, generous negative space at upper quarter, high readability of silhouette, precise elegant shapes. Communicate careful investigation, organized evidence and human judgment rather than attack. No hoodies, masks, padlocks, binary rain, hacker cliches, weapons, dramatic neon or fake readable dashboards. Designed as sidebar artwork for login and account creation. No interface, no typography.

## Regenerar capturas

Use uma nova base fictícia em uma porta dedicada e Playwright disponível no ambiente de QA. Não é dependência do produto. Exemplo no PowerShell, na raiz desta versão:

```powershell
.\scripts\run_local.ps1 -Demo -Database output/demo/capturas-novas.demo.db -Port 5058
# Em outro terminal:
$env:PRESENTATION_BASE_URL='http://127.0.0.1:5058'
node tests/browser_presentation.cjs --capture-only
```

O script grava PNGs em output/qa/presentation. Inspecione as capturas e exporte como WebP otimizado para os dois arquivos públicos. Pillow foi usado apenas como ferramenta local de exportação, não foi adicionado a requirements.txt. A suíte sem --capture-only altera as fixtures: execute-a somente em base descartável recém-criada, nunca na base de ensaio que se quer preservar.
