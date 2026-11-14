// Captura telas reais do Purple Talent rodando com a base de demonstração isolada
// (scripts/prepare_demo.py → output/video/video.demo.db, servidor na porta 5057).
// Gera PNGs 1920px de largura em public/captures. Nada é gravado no banco da equipe.
const {chromium} = require('playwright');
const path = require('node:path');
const fs = require('node:fs');

const BASE = process.env.BASE_URL || 'http://127.0.0.1:5057';
const OUT = path.resolve(__dirname, '..', 'public', 'captures');
fs.mkdirSync(OUT, {recursive: true});

async function shot(page, name, {full = false} = {}) {
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(400);
  await page.screenshot({path: path.join(OUT, name + '.png'), fullPage: full});
  console.log('ok', name);
}

async function login(browser, email, password) {
  const context = await browser.newContext({viewport: {width: 1600, height: 900}, deviceScaleFactor: 1.2, reducedMotion: 'reduce'});
  const page = await context.newPage();
  await page.goto(BASE + '/login');
  await page.getByLabel('E-mail', {exact: true}).fill(email);
  await page.getByLabel('Senha', {exact: true}).fill(password);
  await page.getByRole('button', {name: 'Entrar na plataforma', exact: true}).click();
  await page.waitForLoadState('networkidle');
  return {context, page};
}

(async () => {
  const browser = await chromium.launch();
  try {
    // Visitante
    const guest = await browser.newContext({viewport: {width: 1600, height: 900}, deviceScaleFactor: 1.2, reducedMotion: 'reduce'});
    const g = await guest.newPage();
    await g.goto(BASE + '/'); await shot(g, '01-landing'); await shot(g, '01-landing-full', {full: true});
    await g.goto(BASE + '/opportunities'); await shot(g, '02-vagas');
    await g.locator('article').filter({has: g.getByRole('heading', {name: 'DEMO — Estágio em AppSec'})}).getByRole('link').first().click();
    await shot(g, '03-vaga-detalhe'); await shot(g, '03-vaga-detalhe-full', {full: true});
    await g.goto(BASE + '/labs'); await shot(g, '09-labs-publico');
    await guest.close();

    // Candidato fictício
    const {context: cc, page: c} = await login(browser, 'candidato@demo.invalid', 'demonstracao123');
    await shot(c, '04-minhas-candidaturas'); await shot(c, '04-minhas-candidaturas-full', {full: true});
    const draft = c.getByRole('link', {name: /Continuar|rascunho/i}).first();
    if (await draft.count()) { await draft.click(); await shot(c, '05-formulario'); await shot(c, '05-formulario-full', {full: true}); }
    await c.goto(BASE + '/challenges'); await shot(c, '06-desafios');
    // Interação real: resolver o desafio "Cifra de César" com a resposta do catálogo.
    await c.locator('article', {hasText: 'Texto estranho'}).getByRole('link').click();
    await shot(c, '07-desafio');
    const flag = c.getByLabel(/flag/i).first();
    await flag.click(); await flag.pressSequentially('CTF{base64_nao_e_criptografia}', {delay: 60});
    await shot(c, '07-desafio-digitado');
    await c.getByRole('button', {name: /Enviar|Validar/i}).first().click();
    await shot(c, '07-desafio-correto');
    await c.goto(BASE + '/labs'); await shot(c, '08-labs');
    await c.goto(BASE + '/progress'); await shot(c, '10-progresso');
    await c.goto(BASE + '/ranking'); await shot(c, '11-ranking');
    await cc.close();

    // Equipe / mentoria
    const {context: mc, page: m} = await login(browser, 'mentor@cti.local', process.env.DEMO_MENTOR_PASSWORD || 'mentor123');
    await shot(m, '12-admin'); await shot(m, '12-admin-full', {full: true});
    await m.getByRole('link', {name: /Consultar candidatura de Alex Demo/}).first().click();
    await shot(m, '13-dossie'); await shot(m, '13-dossie-full', {full: true});
    for (const [i, name] of ['Avaliação prática', 'Competências', 'Parecer e feedback'].entries()) {
      await m.getByRole('navigation', {name: 'Seções da candidatura'}).getByRole('link', {name, exact: true}).click();
      await shot(m, `14-dossie-${i + 1}`);
    }
    await m.goto(BASE + '/dashboard'); await shot(m, '15-dashboard'); await shot(m, '15-dashboard-full', {full: true});
    await m.goto(BASE + '/ambientes'); await shot(m, '16-ambientes');
    await m.goto(BASE + '/admin/jobs/new'); await shot(m, '17-editor-vaga');
    await mc.close();
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
