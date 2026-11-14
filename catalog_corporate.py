"""Desafios corporativos para colaboradores de qualquer área (não só tecnologia).

Os cenários são fictícios e se resolvem com raciocínio, cálculo ou critério profissional;
nenhum exige execução de código. Cada resposta segue o formato CTF{...} indicado no briefing
para que o mesmo mecanismo de validação da plataforma seja reaproveitado.
"""
import hashlib

SIDE = 'Corporativo'

CORPORATE_CATALOG = [
    # ---------------------------------------------------------------- Atendimento
    dict(title='Prioridade na fila de chamados', category='Atendimento ao cliente', audience='Colaboradores', points=100,
         description='A central recebeu quatro chamados. A regra da empresa é: 1º indisponibilidade total do serviço; '
                     '2º falha financeira; 3º demais casos, por plano (Ouro, Prata, Bronze) e, em empate, por horário de abertura.\n\n'
                     '#101  plano Bronze  erro cosmético na tela        aberto 08:00\n'
                     '#102  plano Ouro    sistema totalmente fora do ar  aberto 09:30\n'
                     '#103  plano Prata   cobrança duplicada no cartão   aberto 08:45\n'
                     '#104  plano Ouro    dúvida sobre um relatório      aberto 07:50\n\n'
                     'Qual é a ordem de atendimento? Envie CTF{números separados por hífen}, por exemplo CTF{101-102-103-104}.',
         answer='CTF{102-103-104-101}'),
    dict(title='O prazo do SLA', category='Atendimento ao cliente', audience='Colaboradores', points=150,
         description='O contrato prevê primeira resposta em até 4 horas úteis. O atendimento funciona de segunda a sexta, das 08:00 às 18:00, '
                     'sem feriados na semana. Um chamado foi aberto na sexta-feira às 16:00.\n\n'
                     'Até que dia e hora a primeira resposta precisa ser enviada? Envie CTF{dia-Hh}, com o dia em três letras minúsculas '
                     '(seg, ter, qua, qui, sex), por exemplo CTF{ter-9h}.',
         answer='CTF{seg-10h}'),
    # --------------------------------------------------------------------- Vendas
    dict(title='Meta trimestral', category='Vendas e comercial', audience='Colaboradores', points=100,
         description='A meta de vendas do trimestre era de R$ 120.000. O time vendeu R$ 31.500 em janeiro, R$ 38.200 em fevereiro '
                     'e R$ 41.050 em março.\n\nQuantos por cento da meta foram atingidos, arredondando para o inteiro mais próximo? '
                     'Envie CTF{número}.',
         answer='CTF{92}'),
    dict(title='Desconto com margem', category='Vendas e comercial', audience='Colaboradores', points=150,
         description='Um produto custa R$ 600 para a empresa e tem preço de lista de R$ 1.000. A política comercial exige margem bruta '
                     'mínima de 30% sobre o preço de venda (margem = (preço − custo) ÷ preço).\n\n'
                     'Qual é o maior desconto percentual inteiro que ainda respeita a política? Envie CTF{número}.',
         answer='CTF{14}'),
    # ------------------------------------------------------------------------- RH
    dict(title='Banco de horas', category='Recursos humanos', audience='Colaboradores', points=100,
         description='A jornada diária é de 8 horas. Um colaborador trabalhou na semana:\n\n'
                     'segunda  9h30\nterça    8h00\nquarta   10h15\nquinta   7h45\nsexta    8h00\n\n'
                     'Qual é o saldo do banco de horas da semana? Envie CTF{HhMM}, por exemplo CTF{1h05}.',
         answer='CTF{3h30}'),
    dict(title='Pergunta inadequada na entrevista', category='Recursos humanos', audience='Todos', points=150,
         description='Uma entrevista estruturada deve avaliar competências relacionadas à vaga. Qual das perguntas abaixo não deve ser feita?\n\n'
                     'A) Conte uma situação em que você precisou conduzir um conflito na equipe.\n'
                     'B) Você pretende ter filhos nos próximos anos?\n'
                     'C) Como você costuma priorizar tarefas quando tudo parece urgente?\n'
                     'D) Qual foi o maior desafio do seu último projeto e o que você aprendeu?\n\n'
                     'Envie CTF{letra}.',
         answer='CTF{B}'),
    # ------------------------------------------------------------------ Financeiro
    dict(title='Conciliação bancária', category='Financeiro', audience='Colaboradores', points=150,
         description='Ao conciliar o razão com o extrato, os totais não fecharam. Compare os lançamentos de um mesmo dia:\n\n'
                     'RAZÃO    1.250,00 | 380,50 | 2.000,00 | 145,90 | 99,00\n'
                     'EXTRATO  1.250,00 | 380,50 | 2.000,00 | 154,90 | 99,00\n\n'
                     'Qual é o valor da diferença entre os dois lançamentos divergentes? Envie CTF{valor} com vírgula e duas casas, '
                     'por exemplo CTF{12,50}.',
         answer='CTF{9,00}'),
    dict(title='Caixa no vermelho', category='Financeiro', audience='Colaboradores', points=200,
         description='O saldo inicial do mês é R$ 50.000. Movimentações previstas:\n\n'
                     'dia 3   saída   R$ 45.000\ndia 5   entrada R$ 30.000\ndia 10  saída   R$ 40.000\n'
                     'dia 15  entrada R$ 20.000\ndia 20  saída   R$ 10.000\n\n'
                     'Em que dia o caixa fica negativo pela primeira vez e de quantos reais é o déficit nesse dia? '
                     'Envie CTF{dia-valor}, sem pontos, por exemplo CTF{7-1500}.',
         answer='CTF{10-5000}'),
    # --------------------------------------------------------- Jurídico e compliance
    dict(title='Dado pessoal ou não?', category='Jurídico e compliance', audience='Todos', points=100,
         description='Pela LGPD, dado pessoal é a informação relacionada a pessoa natural identificada ou identificável. '
                     'Quais itens abaixo não são dados pessoais?\n\n'
                     'A) CNPJ de uma empresa cliente\n'
                     'B) CPF de um colaborador\n'
                     'C) E-mail nome.sobrenome@empresa.com.br\n'
                     'D) Média salarial agregada de 500 pessoas, sem identificação individual\n'
                     'E) Placa do carro da frota atribuído ao motorista Carlos\n\n'
                     'Envie CTF{letras em ordem alfabética separadas por hífen}, por exemplo CTF{A-B}.',
         answer='CTF{A-D}'),
    dict(title='Convite do fornecedor', category='Jurídico e compliance', audience='Todos', points=150,
         description='Durante uma concorrência, o comprador recebe do fornecedor finalista um convite para uma viagem com todas as despesas pagas. '
                     'Qual a atitude correta segundo um código de conduta comum?\n\n'
                     'A) Aceitar e não comentar com ninguém.\n'
                     'B) Recusar e comunicar o convite ao comitê de ética ou compliance.\n'
                     'C) Aceitar e pagar metade das despesas.\n'
                     'D) Aceitar, mas pedir que um colega assine a decisão da compra.\n\n'
                     'Envie CTF{letra}.',
         answer='CTF{B}'),
    # ----------------------------------------------------------- Logística e operações
    dict(title='Ponto de reposição', category='Logística e operações', audience='Colaboradores', points=150,
         description='Um item tem consumo médio de 40 unidades por dia, prazo de reposição do fornecedor de 9 dias e estoque de segurança de 120 unidades.\n\n'
                     'Ponto de reposição = consumo diário × prazo + estoque de segurança. Em quantas unidades o pedido deve ser disparado? '
                     'Envie CTF{número}.',
         answer='CTF{480}'),
    dict(title='Primeiro a vencer, primeiro a sair', category='Logística e operações', audience='Colaboradores', points=100,
         description='Três lotes de iogurte estão no depósito. A regra FEFO (first expired, first out) manda expedir primeiro o lote de validade mais próxima.\n\n'
                     'Lote A  validade 20/12  entrada 01/11\nLote B  validade 15/12  entrada 05/11\nLote C  validade 10/12  entrada 10/11\n\n'
                     'Qual lote deve sair primeiro? Envie CTF{letra}.',
         answer='CTF{C}'),
    # ------------------------------------------------- Qualidade e segurança do trabalho
    dict(title='Taxa de refugo', category='Qualidade e produção', audience='Colaboradores', points=100,
         description='De um lote de 2.500 peças, 75 foram reprovadas na inspeção. Dessas, 15 foram retrabalhadas e depois aprovadas.\n\n'
                     'Qual é a taxa final de refugo, em porcentagem (peças perdidas ÷ total do lote)? '
                     'Envie CTF{valor} com vírgula, por exemplo CTF{1,5}.',
         answer='CTF{2,4}'),
    dict(title='Hierarquia de controles', category='Saúde e segurança do trabalho', audience='Todos', points=100,
         description='Uma máquina gera ruído acima do limite tolerável. Na hierarquia de controles de risco, as medidas vão da mais eficaz à menos eficaz: '
                     'eliminação, substituição, controles de engenharia, controles administrativos e equipamento de proteção individual.\n\n'
                     'Qual medida deve ser considerada primeiro? Envie CTF{palavra}, em minúsculas e sem acento.',
         answer='CTF{eliminacao}'),
    # ----------------------------------------------------------- Marketing e comunicação
    dict(title='Custo de aquisição', category='Marketing e comunicação', audience='Colaboradores', points=150,
         description='Uma campanha custou R$ 18.000 e trouxe 240 novos clientes. Cada cliente paga em média R$ 150 por mês e permanece 6 meses.\n\n'
                     'CAC = investimento ÷ novos clientes. Receita por cliente = mensalidade × meses. Qual é o CAC e quantas vezes a receita por cliente '
                     'cobre o CAC? Envie CTF{cac-vezes}, por exemplo CTF{50-3}.',
         answer='CTF{75-12}'),
    dict(title='Gargalo do funil', category='Marketing e comunicação', audience='Colaboradores', points=100,
         description='Funil do mês: 20.000 visitantes, 1.000 leads, 250 oportunidades e 50 vendas.\n\n'
                     'Em qual passagem entre etapas a taxa de conversão é a menor? Envie CTF{etapa-etapa} com as palavras visitante, lead, '
                     'oportunidade ou venda, por exemplo CTF{lead-venda}.',
         answer='CTF{visitante-lead}'),
    # ------------------------------------------------------------ Liderança e gestão
    dict(title='Priorização de projetos', category='Liderança e gestão', audience='Colaboradores', points=150,
         description='Um gestor pontuou quatro projetos de 0 a 10. A prioridade é dada pelo índice impacto ÷ esforço.\n\n'
                     'P1  impacto 8  esforço 2\nP2  impacto 9  esforço 9\nP3  impacto 5  esforço 1\nP4  impacto 3  esforço 8\n\n'
                     'Qual projeto deve ser o primeiro? Envie CTF{código}, por exemplo CTF{P9}.',
         answer='CTF{P3}'),
    dict(title='Feedback construtivo', category='Liderança e gestão', audience='Todos', points=100,
         description='Um bom feedback descreve a situação, o comportamento observado e o impacto, sem julgar a pessoa. Qual das frases segue esse modelo?\n\n'
                     'A) Você é muito desorganizado.\n'
                     'B) Na reunião de ontem, o relatório foi entregue dois dias depois do combinado, e isso atrasou a apresentação ao cliente.\n'
                     'C) Todo mundo reclama de você.\n'
                     'D) Preciso que você melhore sua atitude.\n\n'
                     'Envie CTF{letra}.',
         answer='CTF{B}'),
    # ------------------------------------------------------------- Dados e planilhas
    dict(title='Crescimento por região', category='Dados e planilhas', audience='Colaboradores', points=150,
         description='Vendas em milhares de reais, comparando dois anos:\n\n'
                     'Norte  120 → 138\nSul    200 → 224\nLeste  150 → 180\nOeste   80 → 100\n\n'
                     'Qual região teve o maior crescimento percentual (não o maior aumento absoluto)? Envie CTF{região}, com a inicial maiúscula.',
         answer='CTF{Oeste}'),
    # ----------------------------------------- Segurança da informação para todos
    dict(title='Sinais de e-mail falso', category='Segurança da informação', audience='Todos', points=100,
         description='Chegou a mensagem abaixo, supostamente do financeiro:\n\n'
                     'De: financeiro@empresa-pagamentos.co\nAssunto: Última chance, atualize sua senha\n\n'
                     'Prezado usuário, sua conta será bloqueada em 2 horas. Clique em "Atualizar agora" (o link leva a outro endereço) '
                     'e informe sua senha.\nAtt., Departamento Financeiro\n\n'
                     'Observações:\n1) O domínio do remetente não é o da empresa.\n2) Há urgência e ameaça de bloqueio.\n'
                     '3) A saudação é genérica.\n4) A assinatura cita o nome de um departamento.\n'
                     '5) O link exibido leva a um endereço diferente.\n\n'
                     'Quais observações são sinais de alerta? Envie CTF{números em ordem crescente separados por hífen}.',
         answer='CTF{1-2-3-5}'),
    dict(title='Classificação da informação', category='Segurança da informação', audience='Todos', points=100,
         description='A política da empresa define: Pública, Interna e Confidencial. Documentos com impacto financeiro ou estratégico se não divulgados '
                     'de forma controlada são Confidenciais.\n\n'
                     'A) Cardápio do refeitório\nB) Planilha com salários individuais\nC) Manual de processos internos\n'
                     'D) Plano estratégico ainda não anunciado\n\n'
                     'Quais itens são Confidenciais? Envie CTF{letras em ordem alfabética separadas por hífen}.',
         answer='CTF{B-D}'),
]


def seed_corporate_catalog(connection):
    """Insere somente títulos ausentes; nunca altera respostas, pontos ou tentativas existentes."""
    for item in CORPORATE_CATALOG:
        connection.execute(
            'INSERT INTO challenges(title,category,side,points,description,hint,url,flag_hash,audience) '
            'SELECT ?,?,?,?,?,?,?,?,? WHERE NOT EXISTS (SELECT 1 FROM challenges WHERE title=?)',
            (item['title'], item['category'], SIDE, item['points'], item['description'], '', '',
             hashlib.sha256(item['answer'].encode()).hexdigest(), item['audience'], item['title']))
