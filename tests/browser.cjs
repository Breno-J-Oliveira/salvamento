// QA opcional: Playwright é ferramenta de teste, não dependência da aplicação.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const out = path.resolve('output/qa');
fs.mkdirSync(out, {recursive:true});
const results = [];
const stamp = Date.now();
const email = `qa-${stamp}@example.com`;
const password = 'Browser-QA-2026!';
let browser;
async function check(name, run) {
  try { await run(); results.push({name,status:'APROVADO'}); }
  catch(e) { results.push({name,status:'FALHOU',detail:e.message}); throw e; }
}
(async()=>{
  browser = await chromium.launch({channel:'chrome',headless:true});
  const context = await browser.newContext({viewport:{width:1440,height:1000}});
  const page = await context.newPage();
  const errors=[];
  page.on('pageerror', e=>errors.push(e.message));
  const go = route=>page.goto(`http://127.0.0.1:5055${route}`);
  await check('N01 Cadastro e login pelo navegador', async()=>{
    await go('/register');
    await page.getByLabel('Nome',{exact:true}).fill('Pessoa QA '+stamp);
    await page.getByLabel('E-mail',{exact:true}).fill(email);
    await page.getByLabel('Senha',{exact:true}).fill(password);
    await page.getByLabel('Equipe').fill('Equipe QA');
    await page.getByRole('button',{name:'Criar minha conta'}).click();
    await page.waitForURL('**/login');
    await page.getByLabel('E-mail',{exact:true}).fill(email);
    await page.getByLabel('Senha',{exact:true}).fill(password);
    await page.getByRole('button',{name:'Entrar na plataforma'}).click();
    await page.waitForURL('**/challenges');
    assert.equal(await page.locator('h1').textContent(),'Desafios CTF');
  });
  await check('N02 Filtro sem resultados e recuperação',async()=>{
    const search=page.locator('[data-filter]');
    await search.fill('inexistente-qa');
    assert.equal(await page.locator('[data-filter-empty]').isVisible(),true);
    await search.fill('');
    assert.equal(await page.locator('[data-filter-empty]').isVisible(),false);
  });
  await check('N03 Flag incorreta correta e pontos únicos',async()=>{
    await go('/challenge/1');
    await page.getByLabel('Flag',{exact:true}).fill('CTF{errada}');
    await page.getByRole('button',{name:'Validar flag'}).click();
    await page.getByText('Flag incorreta. Tente de novo.').waitFor();
    await page.getByLabel('Flag',{exact:true}).fill('CTF{bem_vindo_ao_purple_lab}');
    await page.getByRole('button',{name:'Validar flag'}).click();
    await page.getByText('Desafio concluído.',{exact:false}).waitFor();
    assert.equal(await page.getByRole('button',{name:'Validar flag'}).count(),0);
  });
  await check('N04 Atualização de perfil persistente',async()=>{
    await go('/profile');
    await page.getByLabel('Equipe',{exact:true}).fill('Equipe Aurora QA');
    await page.getByRole('button',{name:'Salvar alterações'}).click();
    await page.reload();
    assert.equal(await page.getByLabel('Equipe',{exact:true}).inputValue(),'Equipe Aurora QA');
  });
  await check('N05 Participante não acessa mentoria',async()=>{
    assert.equal((await go('/dashboard')).status(),403);
    assert.equal((await go('/ambientes')).status(),403);
  });
  await check('N06 Layout participante 375 768 1440 e fontes locais',async()=>{
    for(const width of [375,768,1440]) {
      await page.setViewportSize({width,height:1000});
      for(const route of ['/challenges','/ranking','/profile','/jobs','/challenge/2']) {
        await go(route);
        await page.evaluate(()=>document.fonts.ready);
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth+1),true,route+' '+width);
        await page.screenshot({path:path.join(out,`participant-${route.replaceAll('/','_')}-${width}.png`),fullPage:true});
      }
    }
    assert.equal(await page.evaluate(()=>document.fonts.check('16px Inter')),true);
  });
  await check('N07 Teclado e salto para conteúdo',async()=>{
    await go('/challenges');
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(()=>document.activeElement.className),'skip');
    await page.keyboard.press('Enter');
    assert.equal(await page.evaluate(()=>document.activeElement.id),'main');
  });
  const mentor = await context.newPage();
  await check('N08 Login mentor e criação de vaga',async()=>{
    await page.getByRole('button',{name:'Sair da conta'}).click();
    await page.waitForURL('**/login');
    await mentor.goto('http://127.0.0.1:5055/login');
    await mentor.getByLabel('E-mail',{exact:true}).fill('mentor@cti.local');
    await mentor.getByLabel('Senha',{exact:true}).fill('mentor123');
    await mentor.getByRole('button',{name:'Entrar na plataforma'}).click();
    await mentor.waitForURL('**/challenges');
    await mentor.goto('http://127.0.0.1:5055/jobs');
    await mentor.getByText('Cadastrar oportunidade',{exact:true}).click();
    await mentor.getByLabel('Título da vaga').fill('Vaga QA '+stamp);
    await mentor.getByLabel('Empresa',{exact:true}).fill('Empresa de teste');
    await mentor.getByLabel('Descrição e requisitos').fill('Vaga de teste automatizado para validar candidatura.');
    await mentor.getByLabel('Pontuação mínima').fill('50');
    await mentor.getByRole('button',{name:'Publicar oportunidade'}).click();
    await mentor.getByRole('heading',{name:'Vaga QA '+stamp}).waitFor();
  });
  await check('N09 Avaliação e dossiê imprimível',async()=>{
    await mentor.goto('http://127.0.0.1:5055/dashboard');
    const link=mentor.getByRole('row').filter({hasText:'Pessoa QA '+stamp}).getByRole('link',{name:'Avaliar',exact:true});
    await link.click();
    await mentor.getByLabel('Raciocínio lógico').selectOption('5');
    await mentor.getByLabel('Observações').fill('Evidência QA de avaliação registrada pela mentoria.');
    await mentor.getByRole('button',{name:'Salvar avaliação'}).click();
    await mentor.getByText('Evidência QA de avaliação registrada pela mentoria.',{exact:true}).waitFor();
    await mentor.emulateMedia({media:'print'});
    await mentor.pdf({path:path.join(out,'dossie-qa.pdf'),format:'A4'});
    await mentor.emulateMedia({media:'screen'});
  });
  await check('N10 Layout mentoria e ambientes vazio',async()=>{
    for(const width of [375,768,1440]) {
      await mentor.setViewportSize({width,height:1000});
      for(const route of ['/dashboard','/jobs','/ambientes']) {
        await mentor.goto('http://127.0.0.1:5055'+route);
        assert.equal(await mentor.evaluate(()=>document.documentElement.scrollWidth <= innerWidth+1),true,route+' '+width);
        await mentor.screenshot({path:path.join(out,`mentor-${route.replaceAll('/','_')}-${width}.png`),fullPage:true});
      }
    }
  });
  await check('N11 Candidatura pelo participante',async()=>{
    await mentor.getByRole('button',{name:'Sair da conta'}).click();
    await mentor.waitForURL('**/login');
    await go('/login');
    await page.getByLabel('E-mail',{exact:true}).fill(email);
    await page.getByLabel('Senha',{exact:true}).fill(password);
    await page.getByRole('button',{name:'Entrar na plataforma'}).click();
    await page.waitForURL('**/challenges');
    await go('/jobs');
    const card=page.locator('article').filter({has:page.getByRole('heading',{name:'Vaga QA '+stamp})});
    await card.getByRole('button',{name:'Candidatar-me'}).click();
    await card.getByText('Candidatura registrada',{exact:false}).waitFor();
  });
  await check('N14 Novas páginas Figma em desktop e celular',async()=>{
    for(const width of [375,1440]) {
      await page.setViewportSize({width,height:1000});
      for(const route of ['/','/labs','/blog','/purple-team']) {
        const response=await go(route);
        assert.equal(response.status(),200);
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth+1),true,route+' '+width);
        await page.screenshot({path:path.join(out,`figma-${route.replaceAll('/','_')||'home'}-${width}.png`),fullPage:true});
      }
    }
  });
  await check('N15 Evolução e relato persistido',async()=>{
    await go('/progress');
    await page.locator('summary').filter({hasText:'Boas-vindas'}).click();
    await page.getByLabel('Relato da investigação').first().fill('Investiguei as pistas e validei a resposta. A melhoria consiste em restringir o acesso aos dados internos.');
    await page.getByRole('button',{name:'Salvar relato'}).first().click();
    await page.getByText('Relato salvo no seu portfólio de aprendizagem.',{exact:true}).waitFor();
    await page.reload();
    assert.equal(await page.locator('summary').filter({hasText:'Relato salvo'}).count()>0,true);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
  });
  await check('N12 Ausência de exceções JavaScript',async()=>assert.deepEqual(errors,[]));
  if(process.env.RUN_DOCKER_TESTS === '1') {
    await check('N13 Laboratório Docker pelo navegador de ponta a ponta',async()=>{
      await go('/challenge/2');
      await page.getByRole('button',{name:'Iniciar ambiente'}).click({timeout:180000});
      const open=page.getByRole('link',{name:'Abrir laboratório',exact:false});
      await open.waitFor({timeout:180000});
      const lab=await context.newPage();
      const address=await open.getAttribute('href');
      await lab.goto(address+'/robots.txt');
      assert.ok((await lab.locator('body').textContent()).includes('/backup-interno'));
      await lab.goto(address+'/backup-interno');
      const flag=(await lab.locator('body').textContent()).replace('FLAG: ','').trim();
      assert.match(flag,/^CTF\{[a-f0-9]+\}$/);
      await page.getByLabel('Flag',{exact:true}).fill(flag);
      await page.getByRole('button',{name:'Validar flag'}).click();
      await page.getByText('Desafio concluído.',{exact:false}).waitFor();
      await page.getByRole('button',{name:'Encerrar ambiente',exact:true}).click({timeout:180000});
      await page.getByRole('button',{name:'Iniciar ambiente'}).waitFor();
      await lab.close();
    });
  }
})().catch(e=>{console.error(e.message);process.exitCode=1;}).finally(async()=>{
  fs.writeFileSync(path.join(out,'browser-results.json'),JSON.stringify(results,null,2));
  console.log(JSON.stringify(results));
  if(browser) await browser.close();
});

