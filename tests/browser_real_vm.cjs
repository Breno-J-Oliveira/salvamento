'use strict';
// Explicit opt-in: consumes and retires one disposable Linux VM in a DEMO database.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const base=process.env.REAL_VM_QA_URL;
assert.ok(/^http:\/\/127\.0\.0\.1:(?!5000(?:\/|$))\d+$/.test(base||''),'Use a dedicated disposable demo server, never the team database.');
assert.equal(process.env.REAL_VM_QA_CONFIRM,'disposable-demo','Explicit disposable VM confirmation is required.');
const out=path.resolve(process.env.REAL_VM_QA_OUTPUT||'output/qa/real-vm');
fs.mkdirSync(out,{recursive:true});
const results=[];let browser;
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function check(name,fn){await fn();results.push({name,status:'APROVADO'});console.log(name);}
async function login(page,mentor=false){
 await page.goto(base+'/login');await page.locator('[name=email]').fill(mentor?'mentor@cti.local':'candidato@demo.invalid');
 await page.locator('[name=password]').fill(mentor?'mentor123':'demonstracao123');
 await page.getByRole('button',{name:'Entrar na plataforma',exact:true}).click();
 await page.waitForURL(u=>!u.pathname.startsWith('/login'));
}
(async()=>{
 browser=await chromium.launch({channel:'chrome',headless:true});
 const candidate=await browser.newContext(),mentor=await browser.newContext();
 const cp=await candidate.newPage(),mp=await mentor.newPage();
 await login(cp);await login(mp,true);
 let sid;
 await check('VM01 Reserva de executor Linux realmente conectado',async()=>{
  for(let i=0;i<90;i++){await cp.goto(base+'/remote-labs');if(await cp.getByRole('button',{name:'Iniciar laboratório',exact:true}).isEnabled())break;await delay(5000);}
  await cp.locator('[name=consent]').check();
  await cp.getByRole('button',{name:'Iniciar laboratório',exact:true}).click();
  await cp.waitForURL(/remote-labs\/\d+$/);sid=Number(cp.url().split('/').pop());
  await mp.goto(base+'/remote-labs/'+sid);
  await mp.getByRole('heading',{name:'Acompanhamento da sessão',exact:true}).waitFor();
 });
 async function command(text){
  const before=await(await candidate.request.get(base+'/remote-labs/'+sid+'/events')).json();
  const last=before.commands.at(-1)?.id||0;
  await cp.locator('[name=command]').fill(text);
  await cp.getByRole('button',{name:'Executar comando',exact:true}).click();
  for(let i=0;i<90;i++){
   const data=await(await candidate.request.get(base+'/remote-labs/'+sid+'/events')).json();
   const row=data.commands.find(c=>c.id>last);
   if(row&&!['queued','running'].includes(row.status)){
    assert.ok(['completed','failed'].includes(row.status),'Command interrupted before result');
    return row;
   }
   await delay(1000);
  }
  throw Error('No result from real Linux executor');
 }
 await check('VM02 Identidade reduzida e virtualizador detectado',async()=>{
  const row=await command('id -u; id -Gn; systemd-detect-virt');
  assert.equal(row.exit_code,0);assert.match(row.output,/1100/);assert.match(row.output,/purplelab/);assert.match(row.output,/qemu/);
 });
 await check('VM03 Leitura real dos artefatos da investigação',async()=>{
  const row=await command('cat access.log');
  assert.equal(row.exit_code,0);assert.match(row.output,/login_failed/);assert.match(row.output,/req-71/);
 });
 if(process.env.REAL_VM_CHECK_SYSTEMD_TESTS==='1')await check('VM04 Dois testes Linux systemd sem skips',async()=>{
  const row=await command('cat linux-tests.json');assert.equal(row.exit_code,0);
  const report=JSON.parse(row.output);assert.equal(report.run,2);assert.equal(report.failures,0);assert.equal(report.errors,0);assert.equal(report.skipped,0);
  fs.writeFileSync(path.join(out,'linux-execution-results.json'),JSON.stringify(report,null,2));
 });
 await check('VM05 Token do agente e cloud-init não legíveis pelo candidato',async()=>{
  const row=await command('for p in /etc/purple-agent/token /var/lib/cloud/instance/user-data.txt; do if test -r "$p"; then echo PRIVATE_READABLE; else echo PRIVATE_BLOCKED; fi; done');
  assert.ok(!row.output.includes('PRIVATE_READABLE'));assert.equal((row.output.match(/PRIVATE_BLOCKED/g)||[]).length,2);
 });
 await check('VM06 Saída para host e internet bloqueada',async()=>{
  for(const target of ['10.0.2.2/5000','1.1.1.1/443']){
   const row=await command("if timeout 4 bash -c 'exec 3<>/dev/tcp/"+target+"'; then echo NETWORK_OPEN; else echo NETWORK_BLOCKED; fi");
   assert.match(row.output,/NETWORK_BLOCKED/);assert.ok(!row.output.includes('NETWORK_OPEN'));
  }
 });
 await check('VM07 Processos filhos isolados no cgroup',async()=>{
  await command('setsid sleep 60 >/dev/null 2>&1 & echo CHILD_STARTED; sleep 1');
  const row=await command("if pgrep -f '^sleep 60$' >/dev/null; then echo CHILD_REMAINS; else echo CHILD_CLEAN; fi");
  assert.match(row.output,/CHILD_CLEAN/);assert.ok(!row.output.includes('CHILD_REMAINS'));
 });
 await check('VM08 Acompanhamento real e observação privada',async()=>{
  await mp.reload();await mp.locator('[data-command-history]').getByText('cat access.log',{exact:true}).waitFor();
  await mp.locator('[name=body]').fill('OBSERVACAO-PRIVADA-QA-REAL');
  await mp.getByRole('button',{name:'Salvar observação',exact:true}).click();
  const data=await(await candidate.request.get(base+'/remote-labs/'+sid+'/events')).json();
  assert.deepEqual(data.notes,[]);
  await cp.screenshot({path:path.join(out,'candidate.png'),fullPage:true});
  await mp.screenshot({path:path.join(out,'observer.png'),fullPage:true});
 });
 await check('VM09 Encerrar sessão preserva histórico e aposenta executor',async()=>{
  await cp.getByRole('button',{name:'Encerrar sessão',exact:true}).click();
  const data=await(await candidate.request.get(base+'/remote-labs/'+sid+'/events')).json();
  assert.equal(data.session.status,'ended');assert.ok(data.commands.length>=6);
 });
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(async()=>{
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2));
 if(browser)await browser.close();
});
