// Optional QA: requires an isolated prepare_demo database at PRESENTATION_BASE_URL.
// Playwright is a QA tool, not a product dependency. Never target a real team database.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.PRESENTATION_BASE_URL;
assert.ok(base, 'Set PRESENTATION_BASE_URL to a disposable demo server; this suite changes its fixtures.');
assert.ok(/^http:\/\/127\.0\.0\.1:(?!5000(?:\/|$))\d+$/.test(base), 'Use a dedicated local demo port, never 5000.');
const out = path.resolve('output/qa/presentation'); fs.mkdirSync(out, { recursive: true });
const captureOnly = process.argv.includes('--capture-only');
const results = [], errors = [], failedRequests = [];
let browser;
async function check(name, fn) {
  try { await fn(); results.push({ name, status: 'APROVADO' }); }
  catch (error) { results.push({ name, status: 'FALHOU', detail: error.message }); throw error; }
}
async function login(page, mentor = false) {
  await page.goto(base + '/login');
  await page.getByLabel('E-mail', { exact: true }).fill(mentor ? 'mentor@cti.local' : 'candidato@demo.invalid');
  await page.getByLabel('Senha', { exact: true }).fill(mentor ? (process.env.DEMO_MENTOR_PASSWORD || 'mentor123') : 'demonstracao123');
  await page.getByRole('button', { name: 'Entrar na plataforma', exact: true }).click();
  await page.waitForURL(mentor ? '**/admin' : '**/my-applications');
}
(async () => {
  browser = await chromium.launch({ channel: 'chrome', headless: true });
  const contextOptions = { viewport: { width: 1200, height: 800 }, reducedMotion: 'reduce' };
  const candidate = await browser.newContext(contextOptions), mentor = await browser.newContext(contextOptions);
  const cp = await candidate.newPage(), mp = await mentor.newPage();
  for (const p of [cp, mp]) {
    p.on('pageerror', e => errors.push(e.message));
    p.on('response', r => { if (r.status() >= 400 && r.url().includes('/static/')) failedRequests.push(r.url()); });
  }
  await check('P01 Base demonstração explícita e vagas públicas', async () => {
    assert.equal((await cp.goto(base + '/opportunities')).status(), 200);
    await cp.getByRole('heading', { name: 'DEMO — Analista SOC Júnior', exact: true }).waitFor();
    await cp.getByRole('heading', { name: 'DEMO — Estágio em AppSec', exact: true }).waitFor();
  });
  await check('P02 Login candidato abre sua jornada e captura real', async () => {
    await login(cp);
    await cp.getByRole('link', { name: /Continuar inscrição/ }).waitFor();
    assert.equal((await cp.locator('body').textContent()).includes('Nota interna sintética'), false);
    await cp.locator('.journey-applications').evaluate(el => window.scrollTo(0, el.getBoundingClientRect().top + scrollY - 110));
    await cp.screenshot({ path: path.join(out, 'product-candidate.png') });
  });
  await check('P03 Mentor acessa evidências sintéticas e captura real', async () => {
    await login(mp, true);
    await mp.getByRole('link', { name: /Consultar candidatura de Alex Demo/ }).click();
    await mp.getByRole('heading', { name: 'Formulário enviado', exact: true }).waitFor();
    await mp.locator('.review-dossier').evaluate(el => window.scrollTo(0, el.getBoundingClientRect().top + scrollY - 110));
    await mp.screenshot({ path: path.join(out, 'product-review.png') });
    for (const target of ['review-answers', 'review-assessment', 'review-rubric', 'review-feedback', 'review-history']) {
      assert.equal(await mp.locator('#' + target).count(), 1);
    }
  });
  if (captureOnly) return;
  await check('P04 Landing e imagens carregam sem recursos ausentes', async () => {
    assert.equal((await cp.goto(base + '/')).status(), 200);
    await cp.getByRole('heading', { name: 'Talento se revela na investigação.' }).waitFor();
    await cp.locator('.presentation-closing').scrollIntoViewIfNeeded();
    await cp.waitForFunction(() => [...document.images].every(i => i.complete && i.naturalWidth > 0));
    assert.equal(await cp.locator('.featured-grid article').count(), 2);
    assert.equal(failedRequests.length, 0, failedRequests.join('\n'));
  });
  await check('P05 Menu mobile, cadastro, Aprender e Escape por teclado', async () => {
    const guest = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const p = await guest.newPage(); await p.goto(base + '/');
    const menu = p.locator('.nav-toggle');
    await menu.focus(); await p.keyboard.press('Enter');
    assert.equal(await menu.getAttribute('aria-expanded'), 'true');
    await p.locator('#site-navigation').getByRole('link', { name: 'Criar perfil', exact: true }).waitFor();
    await p.getByText('Aprender', { exact: true }).click();
    await p.getByRole('link', { name: 'Laboratório', exact: true }).waitFor();
    await p.keyboard.press('Escape');
    assert.equal(await menu.getAttribute('aria-expanded'), 'false');
    assert.equal(await menu.evaluate(el => document.activeElement === el), true);
    await p.screenshot({ path: path.join(out, 'home-mobile.png'), fullPage: true });
    await guest.close();
  });
  await check('P06 Navegação e senha continuam acessíveis sem JS', async () => {
    const plain = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
    const p = await plain.newPage(); await p.goto(base + '/login');
    assert.ok(await p.locator('#site-navigation').isVisible());
    assert.ok(await p.locator('#site-navigation a[href="/register"]').isVisible());
    assert.equal(await p.getByRole('button', { name: 'Mostrar senha' }).count(), 0);
    await plain.close();
  });
  await check('P07 Mostrar/ocultar senha mantém formulário e estado', async () => {
    const p = await candidate.newPage(); await p.goto(base + '/register');
    const input = p.getByLabel('Senha', { exact: true }); await input.fill('senha-sintetica');
    await p.getByRole('button', { name: 'Mostrar senha' }).click();
    assert.equal(await input.getAttribute('type'), 'text');
    assert.equal(await p.getByRole('button', { name: 'Ocultar senha' }).getAttribute('aria-pressed'), 'true');
    await p.getByRole('button', { name: 'Ocultar senha' }).click();
    assert.equal(await input.getAttribute('type'), 'password'); await p.close();
  });
  let applicationId;
  await check('P08 Rascunho persiste, revisão e confirmação funcionam', async () => {
    await cp.goto(base + '/my-applications');
    await cp.getByRole('link', { name: /Continuar inscrição/ }).click();
    await cp.getByRole('radio', { name: 'Request ID', exact: true }).check();
    await cp.getByRole('button', { name: 'Salvar rascunho' }).click();
    await cp.reload(); assert.ok(await cp.getByRole('radio', { name: 'Request ID', exact: true }).isChecked());
    await cp.getByRole('button', { name: 'Revisar inscrição' }).click();
    await cp.getByRole('heading', { name: 'Confira antes de enviar.' }).waitFor();
    await cp.getByRole('button', { name: 'Confirmar candidatura', exact: true }).click();
    await cp.waitForURL('**/my-applications');
    const link = cp.getByRole('link', { name: /Abrir avaliação desta candidatura/ });
    applicationId = Number((await link.getAttribute('href')).match(/my-applications\/(\d+)/)[1]);
  });
  await check('P09 Três etapas são entregues sem Docker e CTA se atualiza', async () => {
    await cp.getByRole('link', { name: /Abrir avaliação desta candidatura/ }).click();
    for (let step = 0; step < 3; step++) {
      await cp.locator('[name=response]').fill('Análise sintética de QA: correlacionaria os identificadores e horários, verificaria a atividade com o responsável e preservaria os registros antes de uma decisão proporcional. Etapa ' + (step + 1));
      await cp.getByRole('button', { name: step < 2 ? 'Registrar etapa e continuar' : 'Concluir e enviar avaliação', exact: true }).click();
    }
    await cp.getByRole('heading', { name: 'Avaliação enviada', exact: true }).waitFor();
    await cp.goto(base + '/my-applications');
    assert.equal(await cp.getByRole('link', { name: /Abrir avaliação desta candidatura/ }).count(), 0);
    await cp.getByText('Sua avaliação já foi entregue.', { exact: false }).waitFor();
  });
  await check('P10 Fila de revisão leva à candidatura entregue', async () => {
    await mp.goto(base + '/admin');
    await mp.locator('.review-workload a[href*="work=ready"]').click();
    await mp.locator(`a[href="/admin/applications/${applicationId}"]`).waitFor();
    assert.equal(await mp.locator('select[name=work]').inputValue(), 'ready');
    await mp.locator(`a[href="/admin/applications/${applicationId}"]`).click();
  });
  await check('P11 Parecer por competência e feedback ficam separados', async () => {
    const form = mp.locator(`form[action="/admin/applications/${applicationId}/rubric"]`);
    for (const key of ['investigation','evidence','decisions','communication']) await form.locator(`[name=${key}]`).selectOption('4');
    await form.locator('[name=justification]').fill('PARECER-PRIVADO-QA: análise sintética relaciona evidências, hipóteses e decisões com limites reconhecidos.');
    await form.getByRole('button', { name: 'Registrar revisão por competência' }).click();
    await mp.getByRole('heading', { name: 'Histórico de revisões' }).waitFor();
    await mp.locator('[name=notes]').fill('NOTA-PRIVADA-QA: conteúdo exclusivo da equipe.');
    await mp.locator('[name=feedback]').fill('Retorno de demonstração: sua análise foi recebida e a equipe propõe uma conversa sobre os critérios de validação.');
    await mp.getByRole('button', { name: 'Salvar etapa e parecer' }).click();
    await cp.goto(base + '/my-applications');
    const body = await cp.locator('body').textContent();
    assert.ok(body.includes('Retorno de demonstração:'));
    assert.equal(body.includes('NOTA-PRIVADA-QA'), false); assert.equal(body.includes('PARECER-PRIVADO-QA'), false);
    await cp.goto(base + `/my-applications/${applicationId}/receipt`);
    assert.equal((await cp.locator('body').textContent()).includes('NOTA-PRIVADA-QA'), false);
    await cp.pdf({ path: path.join(out, 'extrato-sintetico.pdf'), format: 'A4', printBackground: true });
  });
  await check('P12 Autorização preservada nas rotas administrativas', async () => {
    assert.equal((await cp.goto(base + '/admin')).status(), 403);
    assert.equal((await cp.goto(base + `/admin/applications/${applicationId}`)).status(), 403);
  });
  await check('P13 Telas responsivas, âncoras e imagens em 390/768/1440px', async () => {
    for (const width of [390, 768, 1440]) {
      for (const [p, route] of [[cp,'/'],[cp,'/opportunities'],[cp,'/my-applications'],[mp,'/admin'],[mp,`/admin/applications/${applicationId}`]]) {
        await p.setViewportSize({ width, height: 1000 });
        assert.equal((await p.goto(base + route)).status(), 200);
        assert.ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), route + ' overflow at ' + width);
        await p.screenshot({ path: path.join(out, `${route.replaceAll('/','_') || 'home'}-${width}.png`), fullPage: true });
      }
    }
  });
  await check('P14 Zoom equivalente 200% mantém conteúdo e controles', async () => {
    await cp.setViewportSize({ width: 640, height: 450 }); await cp.goto(base + '/');
    assert.ok(await cp.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await cp.getByRole('button', { name: 'Menu', exact: true }).click();
    assert.ok(await cp.getByRole('link', { name: 'Minhas candidaturas', exact: true }).isVisible());
  });
  await check('P15 Sem erros JavaScript nem assets ausentes', async () => {
    assert.deepEqual(errors, []); assert.deepEqual(failedRequests, []);
  });
})().catch(error => { console.error(error.message); process.exitCode = 1; })
  .finally(async () => {
    if (browser) await browser.close();
    fs.writeFileSync(path.join(out, captureOnly ? 'capture-results.json' : 'browser-results.json'), JSON.stringify(results, null, 2));
    console.log(JSON.stringify(results.map(({name,status}) => ({name,status})), null, 2));
  });
