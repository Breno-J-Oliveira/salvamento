// Captura de revisão visual (página inteira) para comparar antes/depois. Uso: node scripts/shots_review.cjs <pasta>
const {chromium} = require('playwright');
const path = require('node:path');
const fs = require('node:fs');
const BASE = 'http://127.0.0.1:5057';
const OUT = path.resolve(process.argv[2] || 'review'); fs.mkdirSync(OUT, {recursive: true});
(async () => {
  const b = await chromium.launch();
  const pub = await b.newPage({viewport: {width: 1440, height: 900}});
  for (const [n, u] of [['home', '/'], ['vagas', '/opportunities'], ['login', '/login'], ['register', '/register']]) {
    await pub.goto(BASE + u); await pub.waitForTimeout(500); await pub.screenshot({path: path.join(OUT, n + '.png'), fullPage: true});
  }
  for (const [email, pw, pages] of [
    ['candidato@demo.invalid', 'demonstracao123', [['cand', '/my-applications'], ['desafios', '/challenges'], ['desafio', '/challenge/3'], ['labs', '/labs'], ['ranking', '/ranking'], ['progress', '/progress'], ['purple', '/purple-team'], ['vaga', '/opportunities/2'], ['blog', '/blog']]],
    ['mentor@cti.local', 'mentor123', [['admin', '/admin'], ['dash', '/dashboard'], ['dossie', '/admin/applications/1'], ['amb', '/ambientes'], ['jobs', '/jobs']]]]) {
    const c = await b.newContext({viewport: {width: 1440, height: 900}}); const p = await c.newPage();
    await p.goto(BASE + '/login'); await p.getByLabel('E-mail', {exact: true}).fill(email); await p.getByLabel('Senha', {exact: true}).fill(pw);
    await p.getByRole('button', {name: 'Entrar na plataforma', exact: true}).click(); await p.waitForLoadState('networkidle');
    for (const [n, u] of pages) { await p.goto(BASE + u); await p.waitForTimeout(400); await p.screenshot({path: path.join(OUT, n + '.png'), fullPage: true}); }
    await c.close();
  }
  await b.close(); console.log('ok');
})().catch(e => { console.error(e.message); process.exit(1); });
