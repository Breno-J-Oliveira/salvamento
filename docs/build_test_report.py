"""Gerador do relatório de QA. Usa python-docx do runtime documental, não do produto."""
import json
from pathlib import Path
from collections import Counter
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=Path('D:/Plano de Testes de Software & GOT (1).docx')
units=json.loads((ROOT/'output/qa/unit-results.json').read_text(encoding='utf-8'))
browser=json.loads((ROOT/'output/qa/browser-results.json').read_text(encoding='utf-8'))
cases=json.loads((ROOT/'docs/casos-got.json').read_text(encoding='utf-8'))
doc=Document(REFERENCE)
body=doc._element.body
for child in list(body):
    if child.tag != qn('w:sectPr'):body.remove(child)
# Reutiliza o formato A4 e as margens de 2,54 cm do modelo fornecido.
normal=doc.styles['normal']
normal.font.name='Arial';normal.font.size=Pt(10)
normal.paragraph_format.space_after=Pt(6)
normal.paragraph_format.line_spacing=1.1
for name,size in [('Title',24),('Heading 1',15),('Heading 2',12)]:
    style=doc.styles[name];style.font.name='Arial';style.font.size=Pt(size);style.font.color.rgb=RGBColor(0,0,0)
    style.paragraph_format.keep_with_next=True
    style.paragraph_format.space_before=Pt(12)
    style.paragraph_format.space_after=Pt(6)
doc.core_properties.title='Plano de Testes de Software e GOT Purple Talent'
doc.core_properties.subject='Integração local e verificação funcional e de segurança'
doc.core_properties.author='Equipe Purple Talent'

def p(text):return doc.add_paragraph(text,style='normal')
def heading(text):doc.add_heading(text,level=1)
def table(headers, rows, widths=None):
    t=doc.add_table(rows=1,cols=len(headers))
    t.autofit=False
    if widths:
        for col,width in zip(t.columns,widths):col.width=Cm(width)
    for cell,text in zip(t.rows[0].cells,headers):
        cell.text=text
        shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E7E6E6');cell._tc.get_or_add_tcPr().append(shade)
        for run in cell.paragraphs[0].runs:run.bold=True
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for values in rows:
        for cell,text in zip(t.add_row().cells,values):cell.text=str(text)
    for row in t.rows:
        no_split=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(no_split)
        if widths:
            for cell,width in zip(row.cells,widths):cell.width=Cm(width)
        for cell in row.cells:
            for para in cell.paragraphs:
                para.paragraph_format.space_after=Pt(4)
                para.paragraph_format.space_before=Pt(4)
                for run in para.runs:run.font.name='Arial';run.font.size=Pt(9)
    return t

doc.add_paragraph('Plano de Testes de Software e GOT',style='Title')
p('Purple Talent | Integração do frontend e dos ambientes Docker')
p('Documento de planejamento, rastreabilidade, execução e resultados para revisão da equipe e da Scrum Master. A verificação cobre a versão local baseada em Flask e SQLite, com laboratórios Docker e a interface derivada das referências da Rafaela.')
heading('Identificação do projeto')
table(['Campo','Identificação'],[
    ['Projeto','Purple Talent — Desafio de Ideias SENAI'],
    ['Data de consolidação','5 de novembro de 2026'],
    ['Responsável pelo projeto','Breno J. Oliveira e equipe'],
    ['Versão avaliada','Integração local da base da equipe; sem publicação GitHub'],
    ['Ambiente','Windows, Python 3.12, Flask 3.0.3, SQLite, Docker Desktop Linux 29.6.2 e Chrome'],
    ['Dados','Bancos temporários nos testes unitários e output/qa/browser.db no navegador; dados demonstrativos'],
    ['Referência','Estrutura do Plano de Testes de Software & GOT fornecido pela equipe; cenários de checkout substituídos pelos do Purple Talent']
],[3.3,12.5])
heading('Resultado da execução')
counts=Counter(r['status'] for r in units+browser)
p(f"Foram registrados {len(units)} testes automatizados de aplicação, limites, laboratório e orquestração, além de {len(browser)} cenários de navegador. Resultado consolidado: "+', '.join(f'{v} {k.lower()}' for k,v in counts.items())+'.')
p('A aprovação destes cenários confirma o comportamento observado nesta configuração. Não equivale a garantia de ausência de falhas, certificação de segurança, aprovação institucional ou autorização de publicação em produção.')
heading('Escopo e estratégia de teste')
p('Foram exercitados cadastro, autenticação, perfil, arenas, validação de flags, pontuação, ranking, avaliação do mentor, dossiê, vagas, candidaturas e ciclo de vida dos ambientes. Os testes combinam cliente HTTP Flask, banco SQLite real temporário, simulações controladas de falhas Docker, execução real de containers e navegação automatizada no Chrome.')
p('Os cenários adversariais incluem escalada de privilégio, acesso a dados e instâncias alheios, injeção SQL, conteúdo HTML malicioso, falsificação de formulário, repetição de operações, dados inválidos, limites de recursos e submissões concorrentes. As simulações de Docker são identificadas separadamente da integração com o daemon real.')
heading('Regras de negócio verificadas')
for text in [
    'Cadastro público cria participante. As permissões são conferidas no servidor usando o papel atual no banco.',
    'Cada desafio pontua uma vez por participante. Respostas erradas não somam pontos; respostas vazias ou extensas são rejeitadas.',
    'A intranet exige uma instância própria e não expirada. Cada instância recebe uma flag aleatória.',
    'Há no máximo dez ambientes ativos e dois por participante. O prazo de cada ambiente é de sessenta minutos.',
    'O encerramento só é registrado após o Docker confirmar a operação. Uma falha não pode aparentar sucesso.',
    'As notas de avaliação devem ser inteiros entre um e cinco. Apenas mentores podem avaliar participantes e gerenciar vagas.',
    'Uma pessoa só pode registrar uma candidatura por vaga; uma vaga pausada não aceita candidatura nova.',
    'A compatibilidade de vaga é a proporção entre pontuação total e pontuação mínima, limitada a cem por cento. Não representa contratação automática.'
]:p(text)
heading('Critérios de aceite e ordem de execução')
p('A ordem de verificação foi: validações e permissões; persistência e regras; laboratório HTTP; orquestrador; build e configuração Compose; dois containers reais; jornada de participante e mentor no navegador; revisão visual em três larguras; fluxo Docker pelo navegador. O critério local é não haver falhas abertas nos cenários executados e registrar explicitamente os limites de cobertura.')
heading('Matriz GOT dos testes automatizados')
p('Cada linha relaciona o identificador ao cenário, dados de entrada, resultado esperado e estado observado. APROVADO significa que todas as asserções daquele método passaram. A rastreabilidade dos métodos está no anexo.')
trace=[]
groups=[('Aplicação e permissões','test_app.'),('Catálogo incremental','test_catalog.'),('Limites e concorrência','test_edge_cases.'),('Laboratório HTTP','test_lab.'),('Progresso e relatos','test_learning.'),('Orquestração Docker','test_orchestrator.')]
index=0
for group,prefix in groups:
    doc.add_heading(group,level=2)
    rows=[]
    for record in units:
        if not record['test'].startswith(prefix):continue
        index+=1; ident=f'CT-{index:02d}'
        key=record['test'].split('.')[-1]
        title,inputs,expected=cases[key]
        rows.append([ident+'\n'+title,inputs,expected,record['status']])
        trace.append((ident,record['test']))
    table(['ID e cenário','Entrada e procedimento','Esperado e verificado','Resultado'],rows,[3.1,4.4,6.1,2.2])

heading('Testes de usuário no navegador')
browser_expected={
'N15':'Abrir evolução, salvar relato de desafio concluído e confirmar persistência após recarregar.',
'N14':'Início, laboratório, blog e Purple Team em 375 e 1440 px, sem overflow horizontal e com HTTP 200.',
'N01':'Preencher cadastro, autenticar e abrir arenas.',
'N02':'Buscar termo inexistente e limpar a busca; estado vazio aparece e desaparece.',
'N03':'Enviar flag errada e correta; conclusão bloqueia novo envio pela tela.',
'N04':'Alterar equipe, recarregar e conferir persistência.',
'N05':'Acessar URLs de mentoria com conta participante; resposta 403.',
'N06':'Arenas, ranking, perfil, vagas e desafio em 375, 768 e 1440 px, sem overflow horizontal da página; fontes locais carregadas.',
'N07':'Usar Tab e Enter no link de salto; foco chega ao conteúdo principal.',
'N08':'Autenticar mentor e cadastrar oportunidade pelo formulário.',
'N09':'Abrir dossiê, salvar avaliação e produzir PDF da versão de impressão.',
'N10':'Painel, vagas e ambientes em 375, 768 e 1440 px, sem overflow da página.',
'N11':'Autenticar participante e registrar candidatura pela tela.',
'N12':'Nenhuma exceção JavaScript na página do participante durante os fluxos.',
'N13':'Iniciar container pela tela, abrir robots.txt, descobrir a flag, submeter e encerrar o ambiente.'}
table(['ID e cenário','Procedimento e resultado esperado','Obtido'],[[r['name'],browser_expected[r['name'][:3]],r['status']] for r in browser],[4.4,9.2,2.2])
p('A inspeção visual das capturas de arenas e mentoria confirmou a identidade escura, os acentos roxo, azul e vermelho, as fontes locais e o reflow mobile. A verificação de teclado cobre o salto de navegação; não foi realizada certificação completa de acessibilidade com leitores de tela.')
heading('Bugs identificados e correções aplicadas')
table(['Problema','Correção e evidência'],[
['Estado perdido na inicialização','Removida a desativação indiscriminada de instâncias. Teste init_preserves_users_and_instances.'],
['Falhas Docker ocultadas','Parada propaga falha; aplicação mantém estado e informa o problema. Testes reaper e stop.'],
['Porta escolhida fora do Docker','Alocação atômica pelo Docker evita a janela entre consultar e ocupar uma porta. Teste de argumentos e dois containers reais.'],
['Falta de proteção dos formulários','Tokens CSRF, validação e limitação de tentativas em POST. Testes de token ausente, errado e limites.'],
['Unicode no token provocava erro interno','Comparação passou a usar bytes UTF-8; token adulterado recebe 400.'],
['Submissão concorrente inconsistente','Transação revalida conclusão e POST de desafio já resolvido redireciona. Reexecução confirmou uma conclusão e dois redirecionamentos.'],
['Notas inválidas geravam erro ou eram ajustadas silenciosamente','Validação explícita de inteiros de 1 a 5, com resposta 400.'],
['Interface desconectada da proposta visual','Templates integrados com cores, fontes locais, navegação, estados vazios, feedback e responsividade.'],
['Falhas no próprio roteiro de QA','Seletor do link de dossiê corrigido para Avaliar; conexões SQLite de testes fechadas explicitamente no Windows. Reexecuções aprovadas.']
],[5,10.8])
p('Os problemas da base foram identificados por revisão de código e pelos testes adicionados. Não foi executada uma bateria completa na versão original; por isso não se atribui retroativamente um status inicial a cada cenário. A primeira execução de concorrência retornou 302 e 200; após o ajuste, ambos retornaram 302 e a contagem de conclusões permaneceu igual a um.')
heading('Reexecução e evidências')
p('A última execução consolidada de unittest foi concluída com o teste Docker real habilitado. Os resultados individuais estão em output/qa/unit-results.json. Os cenários do Chrome estão em output/qa/browser-results.json; capturas PNG e dossie-qa.pdf compõem a evidência local, ignorada pelo Git.')
for command in [
    r'.\.venv\Scripts\python.exe tests/run_report.py',
    r"$env:RUN_DOCKER_TESTS='1' e $env:DOCKER_CONTEXT='desktop-linux' antes da suíte completa",
    r'docker --context desktop-linux compose --profile manual build web01',
    r'docker --context desktop-linux compose --profile manual config --quiet',
    r'node --check static/app.js',
    r'.\.venv\Scripts\python.exe tests/serve_browser.py e node tests/browser.cjs com Playwright disponível'
]:p(command)
heading('Limites de cobertura e recomendações de aceite')
for text in [
    'A execução está limitada ao computador local. O servidor Flask de desenvolvimento não foi homologado para produção ou acesso remoto.',
    'A limpeza de ambientes depende de a aplicação estar em execução. Não houve espera real de sessenta minutos: a expiração foi exercitada com relógio e registros controlados.',
    'Não houve teste de carga prolongado, exaustão real de memória, penetração externa, falha elétrica, restauração de backup ou avaliação em outros sistemas operacionais.',
    'A rede bridge com ICC desabilitado e os limites do container não garantem isolamento absoluto do host ou de toda saída de rede. O laboratório não deve executar código arbitrário enviado por usuários.',
    'O acesso demonstrativo de mentoria e as credenciais legadas foram preservados. A versão local não deve ser exposta à internet.',
    'O relatório foi verificado estruturalmente. A paginação final em Word permanece pendente de revisão: o runtime documental deste Windows não inclui LibreOffice e não possui Word instalado para renderização.',
    'A próxima etapa é o aceite humano da equipe nas telas e regras entregues. Nenhuma publicação GitHub foi efetuada nesta entrega.'
]:p(text)
heading('Anexo de rastreabilidade')
table(['ID','Método automatizado'],trace,[1.7,14.1])
dest=ROOT/'docs'/'Plano de Testes de Software & GOT.docx'
doc.save(dest)
print(str(dest))
print(json.dumps({'unit':len(units),'browser':len(browser),'status':dict(counts)},ensure_ascii=False))
