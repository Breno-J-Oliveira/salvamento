// Produces optional contingency footage using fictional fixtures, after login.
// Requires a prepare_demo server; writes no session/cookie files.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const base=process.env.PRESENTATION_BASE_URL || 'http://127.0.0.1:5057';
assert.ok(/^http:\/\/127\.0\.0\.1:(?!5000(?:\/|$))\d+$/.test(base));
const out=path.resolve('output/qa/presentation/contingencia');fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try{
  for(const role of ['candidato','equipe']){
   const auth=await browser.newContext(),a=await auth.newPage();
   await a.goto(base+'/login');
   await a.getByLabel('E-mail',{exact:true}).fill(role==='candidato'?'candidato@demo.invalid':'mentor@cti.local');
   await a.getByLabel('Senha',{exact:true}).fill(role==='candidato'?'demonstracao123':process.env.DEMO_MENTOR_PASSWORD||'mentor123');
   await a.getByRole('button',{name:'Entrar na plataforma',exact:true}).click();
   await a.waitForURL(role==='candidato'?'**/my-applications':'**/admin');
   const context=await browser.newContext({storageState:await auth.storageState(),viewport:{width:1280,height:800},reducedMotion:'reduce',recordVideo:{dir:out,size:{width:1280,height:800}}});
   const p=await context.newPage(),video=p.video();await auth.close();
   if(role==='candidato'){
    await p.goto(base+'/');await p.waitForTimeout(3500);
    await p.locator('.product-story').scrollIntoViewIfNeeded();await p.waitForTimeout(3500);
    await p.goto(base+'/opportunities');await p.waitForTimeout(3500);
    await p.locator('article').filter({has:p.getByRole('heading',{name:'DEMO — Estágio em AppSec',exact:true})}).getByRole('link').click();await p.waitForTimeout(3500);
    await p.goto(base+'/my-applications');await p.locator('.journey-applications').scrollIntoViewIfNeeded();await p.waitForTimeout(4500);
    await p.getByRole('link',{name:/Consultar minhas respostas para DEMO — Analista SOC/}).click();await p.waitForTimeout(4000);
    await p.pdf({path:path.join(out,'extrato-demonstracao.pdf'),format:'A4',printBackground:true});
   }else{
    await p.goto(base+'/admin');await p.waitForTimeout(4000);
    await p.getByRole('link',{name:/Consultar candidatura de Alex Demo/}).click();await p.waitForTimeout(3000);
    for(const name of ['Respostas','Avaliação prática','Competências','Parecer e feedback','Histórico']){
     await p.getByRole('navigation',{name:'Seções da candidatura'}).getByRole('link',{name,exact:true}).click();await p.waitForTimeout(3000);
    }
   }
   await context.close();await video.saveAs(path.join(out,role+'.webm'));await video.delete();
   console.log('Contingencia sintetica gravada: '+role+'.webm');
  }
 }finally{await browser.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
