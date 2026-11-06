// QA da gestão editorial de vagas. Requer tests/serve_recruitment.py ativo.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');
const base=process.env.RECRUITMENT_BASE_URL||'http://127.0.0.1:5056';
const out=path.resolve('output/qa');fs.mkdirSync(out,{recursive:true});
const stamp=Date.now(),title=`QA Ciclo Vaga ${stamp}`,email=`vacancy-${stamp}@example.test`;
const password='Synthetic-Vacancy-QA-2026!';const results=[];let browser;
async function check(name,fn){try{await fn();results.push({name,status:'APROVADO'});}catch(e){results.push({name,status:'FALHOU',detail:e.message});throw e;}}
(async()=>{
 browser=await chromium.launch({channel:'chrome',headless:true});
 const mentor=await browser.newContext({viewport:{width:1440,height:1000}}),candidate=await browser.newContext({viewport:{width:1440,height:1000}}),anon=await browser.newContext();
 const mp=await mentor.newPage(),cp=await candidate.newPage(),ap=await anon.newPage();const errors=[];
 mp.on('dialog',dialog=>dialog.accept());
 for(const p of [mp,cp,ap])p.on('pageerror',e=>errors.push(e.message));
 const go=(p,url)=>p.goto(base+url);let jid,aid;
 const clickAction=(p,value)=>p.locator(`button[name="action"][value="${value}"]`).click();
 const stateAction=async(state)=>{
   await go(mp,`/admin/jobs/${jid}/edit`);
   const form=mp.locator(`form[action="/admin/jobs/${jid}/state"]`).filter({has:mp.locator(`input[name="state"][value="${state}"]`)});
   await form.locator('button').click();
 };
 await check('V01 Criar rascunho editorial sem exposição pública',async()=>{
  await go(mp,'/login');await mp.locator('[name=email]').fill('mentor@cti.local');await mp.locator('[name=password]').fill('mentor123');await mp.getByRole('button',{name:'Entrar na plataforma'}).click();await mp.waitForURL('**/challenges');
  await go(mp,'/admin/jobs/new');await mp.locator('[name=title]').fill(title);await mp.locator('[name=company]').fill('Empresa fictícia QA');await mp.locator('textarea[name=description]').fill('Descrição sintética para verificar a gestão editorial das vagas.');await mp.locator('[name=side]').selectOption('Blue Team');await mp.locator('[name=min_points]').fill('0');
  await clickAction(mp,'save_draft');await mp.waitForURL(/\/admin/);
  // Tanto redirect para editor quanto para lista preserva link de edição.
  let match=mp.url().match(/\/admin\/jobs\/(\d+)\/edit/);
  if(!match){await go(mp,'/admin');const tr=mp.locator('tr').filter({hasText:title});const href=await tr.locator('a[href$="/edit"]').getAttribute('href');match=href.match(/jobs\/(\d+)/);}
  jid=Number(match[1]);
  assert.equal((await go(ap,`/opportunities/${jid}`)).status(),404);await go(ap,'/opportunities');assert.equal(await ap.getByText(title,{exact:true}).count(),0);
 });
 await check('V02 Prévia da equipe não permite candidatura ao rascunho',async()=>{
  assert.equal((await go(mp,`/admin/jobs/${jid}/preview`)).status(),200);
  assert.equal(await mp.locator(`a[href="/applications/${jid}/form"]`).count(),0);
  await go(ap,`/admin/jobs/${jid}/preview`);assert.ok(ap.url().includes('/login?next='));
 });
 await check('V03 Publicar vaga editada com prazo e metadados',async()=>{
  await go(mp,`/admin/jobs/${jid}/edit`);await mp.locator('[name=location]').fill('São Paulo');await mp.locator('[name=deadline]').fill('2099-12-31');
  await clickAction(mp,'publish');
  assert.equal((await go(ap,`/opportunities/${jid}`)).status(),200);await ap.getByRole('heading',{name:title,exact:true}).waitFor();await ap.getByText('São Paulo',{exact:false}).first().waitFor();
 });
 await check('V04 Candidato salva inscrição antes do encerramento',async()=>{
  await go(cp,'/register');await cp.locator('[name=name]').fill('Pessoa QA Vagas');await cp.locator('[name=email]').fill(email);await cp.locator('[name=password]').fill(password);await cp.getByRole('button',{name:'Criar minha conta'}).click();await cp.waitForURL(/\/login/);
  await cp.locator('[name=email]').fill(email);await cp.locator('[name=password]').fill(password);await cp.getByRole('button',{name:'Entrar na plataforma'}).click();await cp.waitForURL('**/challenges');
  await go(cp,`/applications/${jid}/form`);await cp.locator('[name=q_availability]').fill('Horário comercial');await cp.locator('[name=q_experience]').fill('Projeto sintético de investigação de logs e alertas.');await cp.getByRole('button',{name:'Revisar inscrição'}).click();await cp.waitForURL(`**/applications/${jid}/review`);
 });
 await check('V05 Pausa preserva rascunho e bloqueia confirmação',async()=>{
  await stateAction('paused');
  await cp.getByRole('button',{name:'Confirmar candidatura'}).click();assert.equal(cp.url().includes(`/applications/${jid}/review`),true);await cp.getByText(/encerrad|recebendo|inscriç|pausad/i).first().waitFor();
  await go(cp,'/my-applications');await cp.locator('article').filter({hasText:title}).getByRole('link',{name:'Continuar inscrição'}).waitFor();
  assert.equal((await go(ap,`/opportunities/${jid}`)).status(),404);
 });
 await check('V06 Reabertura explícita permite enviar sem perder respostas',async()=>{
  await stateAction('published');await go(cp,`/applications/${jid}/form`);assert.equal(await cp.locator('[name=q_availability]').inputValue(),'Horário comercial');await cp.getByRole('button',{name:'Revisar inscrição'}).click();await cp.waitForURL(`**/applications/${jid}/review`);await cp.getByRole('button',{name:'Confirmar candidatura'}).click();await cp.waitForURL('**/my-applications');
  const href=await cp.locator('article').filter({hasText:title}).locator('a[href$="/assessment"]').getAttribute('href');aid=Number(href.match(/applications\/(\d+)/)[1]);
 });
 await check('V07 Encerramento mantém avaliação da candidatura enviada',async()=>{
  await stateAction('closed');assert.equal((await go(cp,`/my-applications/${aid}/assessment`)).status(),200);await cp.getByLabel('Sua análise',{exact:true}).waitFor();
  assert.equal((await go(ap,`/opportunities/${jid}`)).status(),200);assert.equal(await ap.locator(`a[href="/applications/${jid}/form"]`).count(),0);
 });
 await check('V08 Edição simultânea não sobrescreve a alteração mais recente',async()=>{
  const second=await mentor.newPage();await go(mp,`/admin/jobs/${jid}/edit`);await go(second,`/admin/jobs/${jid}/edit`);await mp.locator('textarea[name=description]').fill('Descrição atualizada primeiro pela equipe para avaliar conflitos de edição.');await clickAction(mp,'save');
  await second.locator('textarea[name=description]').fill('Descrição de outra aba que não pode sobrescrever uma atualização mais recente.');
  const response=await Promise.all([second.waitForResponse(r=>r.url().endsWith(`/admin/jobs/${jid}/edit`)&&r.request().method()==='POST'),clickAction(second,'save')]);assert.equal(response[0].status(),409);
  assert.equal(await second.locator('textarea[name=description]').inputValue(),'Descrição de outra aba que não pode sobrescrever uma atualização mais recente.');await go(mp,`/admin/jobs/${jid}/edit`);assert.equal(await mp.locator('textarea[name=description]').inputValue(),'Descrição atualizada primeiro pela equipe para avaliar conflitos de edição.');await second.close();
 });
 await check('V09 Editor e encerramento acessíveis em mobile e desktop',async()=>{
  for(const width of [390,1440]){await mp.setViewportSize({width,height:1000});await ap.setViewportSize({width,height:1000});for(const[p,route]of [[mp,`/admin/jobs/${jid}/edit`],[mp,'/admin'],[ap,`/opportunities/${jid}`]]){await go(p,route);assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true,route);await p.screenshot({path:path.join(out,`vacancies-${route.replaceAll('/','_')}-${width}.png`),fullPage:true});}}
 });
 await check('V10 Nenhuma exceção JavaScript',async()=>assert.deepEqual(errors,[]));
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(async()=>{fs.writeFileSync(path.join(out,'vacancies-browser-results.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results));if(browser)await browser.close();});
