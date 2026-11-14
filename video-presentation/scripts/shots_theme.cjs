// Capturas de revisão nos temas escuro e claro. Uso: node scripts/shots_theme.cjs <pasta>
const {chromium} = require('playwright');
const path = require('node:path'); const fs = require('node:fs');
const B = 'http://127.0.0.1:5057'; const OUT = path.resolve(process.argv[2] || 'review-theme'); fs.mkdirSync(OUT, {recursive: true});
(async () => {
  const b = await chromium.launch(); const errs = [];
  for (const theme of ['dark', 'light']) {
    const c = await b.newContext({viewport: {width: 1440, height: 900}, colorScheme: theme});
    const p = await c.newPage(); p.on('console', m => { if (m.type() === 'error') errs.push(theme + ': ' + m.text()); });
    await p.goto(B + '/'); await p.evaluate(() => document.querySelectorAll('.reveal').forEach(e => e.classList.add('in'))); await p.waitForTimeout(800);
    await p.screenshot({path: path.join(OUT, theme + '-home.png'), fullPage: true});
    for (const [n, u] of [['vagas', '/opportunities'], ['login', '/login']]) { await p.goto(B + u); await p.waitForTimeout(300); await p.screenshot({path: path.join(OUT, `${theme}-${n}.png`)}); }
    await p.goto(B + '/login'); await p.getByLabel('E-mail', {exact: true}).fill('mentor@cti.local'); await p.getByLabel('Senha', {exact: true}).fill('mentor123');
    await p.getByRole('button', {name: 'Entrar na plataforma'}).click(); await p.waitForLoadState('networkidle');
    for (const [n, u] of [['admin', '/admin'], ['dossie', '/admin/applications/1'], ['blog', '/admin/blog'], ['ranking', '/ranking'], ['desafios', '/challenges']]) { await p.goto(B + u); await p.waitForTimeout(300); await p.screenshot({path: path.join(OUT, `${theme}-${n}.png`)}); }
    await c.close();
  }
  // alternância pelo botão
  const c = await b.newContext({viewport: {width: 1440, height: 900}, colorScheme: 'dark'}); const p = await c.newPage();
  await p.goto(B + '/'); const before = await p.evaluate(() => document.documentElement.dataset.theme);
  await p.click('[data-theme-toggle]'); await p.reload(); const after = await p.evaluate(() => document.documentElement.dataset.theme);
  console.log('toggle', before, '->', after, 'errors', errs);
  await b.close();
})().catch(e => { console.error(e.message); process.exit(1); });
