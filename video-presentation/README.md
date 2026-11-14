# Vídeo de apresentação — Purple Talent

Vídeo institucional de 88 s (1920×1080, 30 fps, H.264 + AAC): `out/Purple-Talent-Apresentacao.mp4`.

## Roteiro

| Tempo | Cena | Conteúdo (telas reais) |
|---|---|---|
| 0–7 s | Abertura | Marca Purple Talent, barras Red · Purple · Blue |
| 7–18 s | Proposta | Problema → pilares Prática, Evidências, Avaliação humana |
| 18–36 s | Candidato | Vagas → detalhe da vaga → formulário com rascunho → minhas candidaturas |
| 36–52 s | Prática | Catálogo CTF → flag digitada → validação correta → laboratórios VirtualBox |
| 52–68 s | Avaliação humana | Fluxo Respostas → Evidências → Rubrica → Feedback; dossiê, competências, parecer |
| 68–80 s | Gestão | Painel admin, avaliação Purple Team, ranking, ambientes virtuais |
| 80–88 s | Encerramento | Slogan do rodapé do site |

A plataforma não tem recursos de IA, então a cena "IA" do modelo foi trocada pelo diferencial real: a avaliação humana por rubrica.

## Como regenerar

```powershell
# 1. base de demonstração isolada (nunca usa lab.db)
python scripts/prepare_demo.py output/video/video.demo.db
# 2. servidor da demo
$env:LAB_DATABASE="$PWD\output\video\video.demo.db"; $env:PORT="5057"; python app.py
# 3. em video-presentation/
npm install
npx playwright install chromium
npm run capture   # telas reais → public/captures
npm run music     # trilha original → public/audio/trilha.wav
npm run studio    # pré-visualização interativa
npm run render    # gera out/Purple-Talent-Apresentacao.mp4
```

`npm run capture` resolve o desafio "Texto estranho" na base de demonstração. Para capturar de novo, use uma base nova.

## Manutenção

- Durações das cenas: `SCENES`, em `src/Video.tsx`.
- Textos, capturas e câmera (zoom/foco por keyframes `{s, x, y}`): `src/scenes/scenes.tsx`.
- Cores e fontes do site: `src/theme.ts`.
- Trilha: `scripts/music.cjs`, sintetizada por código e livre de direitos.
