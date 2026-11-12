'use strict';
// Protocol/browser QA uses synthetic agent replies, never executes shell commands.
const {chromium, request} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = 'http://127.0.0.1:5071';
const out = path.resolve('output/qa/remote-labs');
fs.mkdirSync(out, {recursive:true});
const results = [];
let browser;
async function check(name, fn) {
  await fn(); results.push({name,status:'passed'}); console.log(name);
}
async function login(page, email, password) {
  await page.goto(base+'/login');
  await page.locator('[name=email]').fill(email);
  await page.locator('[name=password]').fill(password);
  await page.getByRole('button',{name:'Entrar na plataforma',exact:true}).click();
  await page.waitForURL(url=>!url.pathname.startsWith('/login'));
}
(async()=>{
  browser = await chromium.launch({channel:'chrome',headless:true});
  const participant = await browser.newContext();
  const mentor = await browser.newContext();
  const other = await browser.newContext();
  const cp = await participant.newPage();
  const mp = await mentor.newPage();
  const op = await other.newPage();
  const errors = [];
  for(const page of [cp,mp,op]) page.on('pageerror',error=>errors.push(error.message));
  const agent = await request.newContext({baseURL:base,extraHTTPHeaders:{Authorization:'Bearer browser-fixture-agent-1-'+'x'.repeat(32)}});
  const poll = async result => {
    const response=await agent.post('/api/lab-agent/poll',{data:{result:result||null}});
    assert.equal(response.status(),200);return response.json();
  };
  let sid;
  await check('R01 Login e disponibilidade verdadeira',async()=>{
    await login(cp,'candidato@demo.invalid','demonstracao123');
    await login(mp,'mentor@cti.local','mentor123');
    await cp.goto(base+'/remote-labs');
    assert.equal(await cp.getByRole('button',{name:'Iniciar laboratório',exact:true}).isDisabled(),true);
    await poll(); await cp.reload();
    assert.equal(await cp.getByRole('button',{name:'Iniciar laboratório',exact:true}).isEnabled(),true);
  });
  await check('R02 Consentimento e reserva de sessão',async()=>{
    await cp.locator('[name=consent]').check();
    await cp.getByRole('button',{name:'Iniciar laboratório',exact:true}).click();
    await cp.waitForURL(/remote-labs\/\d+$/);sid=Number(cp.url().split('/').pop());
    await cp.getByRole('heading',{name:'Seu terminal de investigação'}).waitFor();
    await mp.goto(base+`/remote-labs/${sid}`);
    assert.equal(await mp.locator('[data-command-form]').count(),0);
    await mp.getByRole('heading',{name:'Acompanhamento da sessão'}).waitFor();
  });
  await check('R03 Comando e resultado observáveis sem recarregar mentor',async()=>{
    await cp.locator('[name=command]').fill('cat access.log');
    await cp.getByRole('button',{name:'Executar comando',exact:true}).click();
    const reply=await poll(); assert.equal(reply.job.command,'cat access.log');
    await poll({command_id:reply.job.command_id,lease_token:reply.job.lease_token,output:'SAÍDA SINTÉTICA QA\n<script>window.qaInjected=true</script>\n'+'registro-longo-'.repeat(50),exit_code:0});
    await mp.locator('[data-command-history] pre').filter({hasText:'SAÍDA SINTÉTICA QA'}).waitFor();
    await cp.locator('[data-command-history] pre').filter({hasText:'SAÍDA SINTÉTICA QA'}).waitFor();
    assert.equal(await mp.evaluate(()=>window.qaInjected),undefined);
    const data=await (await participant.request.get(base+`/remote-labs/${sid}/events`)).json();
    assert.equal(JSON.stringify(data).includes('lease_token'),false);
  });
  await check('R04 Notas privadas e isolamento de participantes',async()=>{
    await mp.locator('[name=body]').fill('NOTA-PRIVADA-REMOTE-QA');
    await mp.getByRole('button',{name:'Salvar observação',exact:true}).click();
    await mp.getByText('NOTA-PRIVADA-REMOTE-QA',{exact:true}).waitFor();
    await cp.reload();assert.equal((await cp.locator('body').textContent()).includes('NOTA-PRIVADA-REMOTE-QA'),false);
    const data=await (await participant.request.get(base+`/remote-labs/${sid}/events`)).json();assert.deepEqual(data.notes,[]);
    await op.goto(base+'/register');
    await op.locator('[name=name]').fill('Pessoa fictícia QA');
    await op.locator('[name=email]').fill('remote-qa@example.invalid');
    await op.locator('[name=password]').fill('senha-ficticia-qa-123');
    await op.locator('form button[type=submit], form button:not([type])').last().click();
    await op.waitForURL(url=>!url.pathname.startsWith('/register'));
    await login(op,'remote-qa@example.invalid','senha-ficticia-qa-123');
    assert.equal((await op.goto(base+`/remote-labs/${sid}`)).status(),403);
    assert.equal((await other.request.get(base+`/remote-labs/${sid}/events`)).status(),403);
  });
  await check('R05 Layout 390 768 1440 e terminal seguro',async()=>{
    for(const width of [390,768,1440]){
      for(const [page,label,route] of [[cp,'participant',`/remote-labs/${sid}`],[mp,'observer',`/remote-labs/${sid}`],[mp,'list','/remote-labs']]){
        await page.setViewportSize({width,height:1000});await page.goto(base+route);
        assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`${label} ${width}`);
        await page.screenshot({path:path.join(out,`${label}-${width}.png`),fullPage:true});
      }
    }
  });
  await check('R06 Encerramento preserva histórico e retira executor',async()=>{
    await mp.goto(base+`/remote-labs/${sid}`);
    await mp.getByRole('button',{name:'Encerrar sessão',exact:true}).click();
    await cp.reload();assert.equal(await cp.getByRole('button',{name:'Executar comando',exact:true}).isDisabled(),true);
    assert.equal((await poll()).state,'retired');
    assert.ok((await cp.locator('[data-command-history]').textContent()).includes('SAÍDA SINTÉTICA QA'));
    assert.equal(await cp.locator('[data-end-form]').isVisible(),false);
  });
  await check('R07 Sem erros JavaScript',async()=>assert.deepEqual(errors,[]));
  await agent.dispose();
})().catch(error=>{console.error(error);results.push({status:'failed',error:error.message});process.exitCode=1;}).finally(async()=>{
  if(browser)await browser.close();fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2));
});


