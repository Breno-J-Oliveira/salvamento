// QA opcional: usa Playwright já disponível em NODE_PATH ou instalado no ambiente de QA.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const base=process.env.RECRUITMENT_BASE_URL || 'http://127.0.0.1:5056';
const out=path.resolve('output/qa');fs.mkdirSync(out,{recursive:true});
const stamp=Date.now(),title=`QA Fluxo SOC ${stamp}`,email=`recruitment-${stamp}@example.com`;
const password='Recruitment-QA-2026!';
const results=[];let browser;
async function check(name,fn){try{await fn();results.push({name,status:'APROVADO'});}catch(e){results.push({name,status:'FALHOU',detail:e.message});throw e;}}
(async()=>{
 browser=await chromium.launch({channel:'chrome',headless:true});
 const mentor=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 const candidate=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 const mp=await mentor.newPage(),cp=await candidate.newPage(),errors=[];
 for(const p of [mp,cp])p.on('pageerror',e=>errors.push(e.message));
 let jid,aid;const demoIds=[];
 const go=(p,route)=>p.goto(base+route);
 await check('R01 Vagas públicas disponíveis sem autenticação',async()=>{
  assert.equal((await go(cp,'/opportunities')).status(),200);
  await cp.getByText('DEMO QA — SOC Júnior',{exact:true}).waitFor();
  await cp.getByText('DEMO QA — Estágio AppSec',{exact:true}).waitFor();
  for(const title of ['DEMO QA — SOC Júnior','DEMO QA — Estágio AppSec']){const href=await cp.locator('article').filter({has:cp.getByRole('heading',{name:title,exact:true})}).getByRole('link').first().getAttribute('href');demoIds.push(Number(href.match(/\d+/)[0]));}
 });
 await check('R02 Mentor cria vaga e configura perguntas próprias',async()=>{
  await go(mp,'/login');await mp.getByLabel('E-mail',{exact:true}).fill('mentor@cti.local');await mp.getByLabel('Senha',{exact:true}).fill('mentor123');
  await mp.getByRole('button',{name:'Entrar na plataforma'}).click();await mp.waitForURL('**/admin');
  await go(mp,'/jobs');await mp.locator('summary').filter({hasText:'Cadastrar oportunidade'}).click();
  await mp.locator('[name=title]').fill(title);await mp.locator('[name=company]').fill('Empresa fictícia de QA');
  await mp.locator('textarea[name=description]').fill('Vaga sintética para validar inscrição, revisão e feedback sem dados reais.');
  await mp.getByRole('button',{name:'Publicar oportunidade'}).click();await mp.waitForURL('**/jobs');
  await go(mp,'/opportunities');const card=mp.locator('article').filter({has:mp.getByRole('heading',{name:title,exact:true})});
  const href=await card.getByRole('link').first().getAttribute('href');jid=Number(href.match(/\d+/)[0]);
  await go(mp,`/admin/jobs/${jid}/form`);
  const rows=mp.locator('[data-question-row]');await rows.first().waitFor();
  await rows.nth(0).locator('[data-question-label]').fill('Disponibilidade para esta vaga');
  await rows.nth(0).locator('[data-question-type]').selectOption('select');
  await rows.nth(0).locator('[data-question-required]').check();
  await rows.nth(0).locator('[data-question-options]').fill('Manhã\nTarde');
  await rows.nth(0).locator('[data-question-answer]').selectOption('Tarde');
  await rows.nth(1).locator('[data-question-label]').fill('Como investigaria um alerta?');
  await rows.nth(1).locator('[data-question-type]').selectOption('textarea');
  await rows.nth(1).locator('[data-question-required]').check();
  await mp.getByRole('button',{name:'Salvar perguntas',exact:true}).click();await mp.waitForURL('**/admin');
  await go(mp,`/admin/jobs/${jid}/form`);assert.equal(await mp.locator('[data-question-row]').first().locator('[data-question-answer]').inputValue(),'Tarde');
 });
 await check('R03 Cadastro e login preservam a vaga escolhida',async()=>{
  await go(cp,`/opportunities/${jid}`);await cp.locator(`a[href="/applications/${jid}/form"]`).click();
  await cp.waitForURL(/\/login\?next=/);assert.ok(cp.url().includes(encodeURIComponent(`/applications/${jid}/form`))||cp.url().includes(`/applications/${jid}/form`));
  await cp.locator('.auth-link a').click();
  await cp.getByLabel('Nome',{exact:true}).fill('Candidato QA Sintético');await cp.getByLabel('E-mail',{exact:true}).fill(email);
  await cp.getByLabel('Senha',{exact:true}).fill(password);await cp.getByRole('button',{name:'Criar minha conta'}).click();
  await cp.waitForURL(/\/login/);await cp.getByLabel('E-mail',{exact:true}).fill(email);await cp.getByLabel('Senha',{exact:true}).fill(password);
  await cp.getByRole('button',{name:'Entrar na plataforma'}).click();await cp.waitForURL(`**/applications/${jid}/form`);
  await cp.getByRole('radio',{name:'Tarde'}).waitFor();
  assert.equal(await cp.getByText('Gabarito:',{exact:false}).count(),0);
 });
 await check('R04 Revisão rejeita ausência obrigatória e mantém formulário',async()=>{
  await cp.getByRole('button',{name:'Revisar inscrição'}).click();
  await cp.getByText('Responda a esta pergunta para continuar.').first().waitFor();
  assert.ok(cp.url().endsWith(`/applications/${jid}/form`));
 });
 await check('R05 Rascunho persiste e confirmação acontece depois da revisão',async()=>{
  await cp.getByRole('radio',{name:'Tarde'}).check();
  await cp.locator('[name=q_experience]').fill('Analisaria origem, contexto, identidade e sequência dos eventos antes de decidir pela contenção.');
  await cp.getByRole('button',{name:'Salvar rascunho'}).click();await cp.getByText('Rascunho recuperado.',{exact:false}).waitFor();
  await cp.reload();assert.ok(await cp.getByRole('radio',{name:'Tarde'}).isChecked());
  await cp.getByRole('button',{name:'Revisar inscrição'}).click();await cp.waitForURL(`**/applications/${jid}/review`);
  await cp.getByRole('heading',{name:'Confira antes de enviar.'}).waitFor();
  await cp.getByRole('button',{name:'Confirmar candidatura'}).click();await cp.waitForURL('**/my-applications');
  await cp.getByRole('heading',{name:title,exact:true}).waitFor();
 });
 await check('R06 Avaliação seletiva completa três etapas em ordem',async()=>{
  const link=cp.getByRole('link',{name:'Abrir avaliação desta candidatura'}).first();
  const href=await link.getAttribute('href');aid=Number(href.match(/\d+/)[0]);await link.click();
  for(let step=0;step<3;step++){
   await cp.getByLabel('Sua análise',{exact:true}).fill(`Etapa ${step+1}: correlacionaria os registros, validaria a hipótese com o responsável e documentaria os limites antes de definir a resposta. Evidência seletiva QA.`);
   await cp.getByRole('button',{name:step===2?'Concluir e enviar avaliação':'Registrar etapa e continuar',exact:true}).click();
  }
  await cp.getByRole('heading',{name:'Avaliação enviada',exact:true}).waitFor();
  await cp.reload();await cp.getByRole('heading',{name:'Avaliação enviada',exact:true}).waitFor();
 });
 await check('R07 Mentor consulta respostas e registra nota restrita e feedback público',async()=>{
  await go(mp,'/admin');const entry=mp.locator('tr').filter({hasText:title}).filter({hasText:'Candidato QA Sintético'});
  const link=entry.getByRole('link').first();const href=await link.getAttribute('href');aid=Number(href.match(/\d+/)[0]);await link.click();
  await mp.getByText('Analisaria origem, contexto, identidade e sequência dos eventos antes de decidir pela contenção.',{exact:true}).waitFor();
  await mp.getByText('1 de 1 respostas correspondem ao gabarito.',{exact:false}).waitFor();
  await mp.locator('[name=status]').selectOption('interview');await mp.locator('[name=notes]').fill('QA-NOTA-INTERNA-RESTRITA-'+stamp);
  await mp.locator('[name=feedback]').fill('Análise recebida. Próxima etapa: entrevista com a equipe.');
  await mp.getByRole('button',{name:'Salvar etapa e parecer'}).click();await mp.waitForURL(`**/admin/applications/${aid}`);
 });
 await check('R12 Rubrica interna registra competências e preserva histórico',async()=>{
  await go(mp,`/admin/applications/${aid}`);
  const form=mp.locator(`form[action="/admin/applications/${aid}/rubric"]`);
  for(const key of ['investigation','evidence','decisions','communication'])await form.locator(`[name=${key}]`).selectOption('4');
  await form.locator('[name=justification]').fill('QA-RUBRICA-INTERNA: as respostas apresentam evidências correlacionadas e decisões justificadas com limites explícitos.');
  await form.getByRole('button',{name:'Registrar revisão por competência'}).click();
  await mp.waitForURL(`**/admin/applications/${aid}`);
  await mp.getByText('Histórico de revisões',{exact:true}).waitFor();
  await mp.reload();assert.equal(await mp.locator('summary').filter({hasText:'Revisão 1'}).count(),1);
 });
 await check('R13 Filtros do painel preservam busca e estado vazio',async()=>{
  await go(mp,'/admin');
  await mp.getByLabel('Buscar candidato ou vaga').fill(title);
  await mp.getByRole('combobox',{name:/^Etapa/}).selectOption('interview');
  await mp.getByRole('button',{name:'Filtrar candidaturas'}).click();
  await mp.getByRole('link',{name:'Consultar candidatura de Candidato QA Sintético'}).waitFor();
  assert.equal(await mp.getByLabel('Buscar candidato ou vaga').inputValue(),title);
  await mp.getByLabel('Buscar candidato ou vaga').fill('sem-resultado-qa-xyz');
  await mp.getByRole('button',{name:'Filtrar candidaturas'}).click();
  await mp.getByText('Nenhuma candidatura corresponde aos filtros.',{exact:false}).waitFor();
 });
 await check('R14 Histórico identifica atores e datas sem replicar notas internas',async()=>{
  await go(mp,`/admin/applications/${aid}`);
  const history=mp.getByRole('list',{name:'Mudanças de etapa da candidatura'});
  await history.waitFor();
  const text=await history.textContent();
  assert.ok(text.includes('Candidato QA Sintético'));
  assert.ok(text.includes('Mentor'));
  assert.equal(text.includes('QA-NOTA-INTERNA'),false);
  assert.ok(await history.locator('time').count()>=2);
 });
 await check('R08 Candidato recebe feedback sem nota interna e não acessa administração',async()=>{
  await go(cp,'/my-applications');await cp.getByText('Análise recebida. Próxima etapa: entrevista com a equipe.',{exact:true}).waitFor();
  assert.equal((await cp.locator('body').textContent()).includes('QA-NOTA-INTERNA-RESTRITA-'),false);
  assert.equal((await cp.locator('body').textContent()).includes('QA-RUBRICA-INTERNA'),false);
  assert.equal((await go(cp,`/admin/applications/${aid}`)).status(),403);assert.equal((await go(cp,'/admin')).status(),403);
 });
 await check('R09 Mobile e desktop sem overflow nas telas novas',async()=>{
  for(const width of [390,1440]){await cp.setViewportSize({width,height:1000});await mp.setViewportSize({width,height:1000});
   for(const [p,route]of [[cp,'/'],[cp,'/opportunities'],[cp,`/opportunities/${jid}`],[cp,'/my-applications'],[mp,'/admin'],[mp,`/admin/jobs/${jid}/form`],[mp,`/admin/applications/${aid}`]]){
    assert.equal((await go(p,route)).status(),200,route);
    assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true,route+' '+width);
    await p.screenshot({path:path.join(out,`recruitment-${route.replaceAll('/','_')||'home'}-${width}.png`),fullPage:true});
   }
  }
 });
 await check('R10 Formulários de SOC e AppSec usam perguntas distintas',async()=>{
  await go(cp,`/applications/${demoIds[0]}/form`);await cp.getByLabel('Experiência com investigação de logs e alertas',{exact:false}).waitFor();
  await go(cp,`/applications/${demoIds[1]}/form`);await cp.getByLabel('Experiência com revisão de código e aplicações',{exact:false}).waitFor();
 });
 await check('R15 Candidato confirma desistência e equipe acompanha o estado',async()=>{
  await go(cp,'/my-applications');
  const card=cp.locator('article').filter({has:cp.getByRole('heading',{name:title,exact:true})});
  await card.getByText('Desistir desta candidatura',{exact:true}).click();
  await card.getByRole('button',{name:'Confirmar desistência'}).click();
  await cp.getByText('Você desistiu desta candidatura.',{exact:false}).waitFor();
  await go(mp,`/admin/applications/${aid}`);
  await mp.getByText('O candidato desistiu; esta candidatura não pode ser reativada pelo parecer.').waitFor();
  assert.equal(await mp.locator('[name=status] option').count(),1);
 });
 await check('R11 Nenhuma exceção JavaScript no percurso',async()=>assert.deepEqual(errors,[]));
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(async()=>{
 fs.writeFileSync(path.join(out,'recruitment-browser-results.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results));if(browser)await browser.close();
});
