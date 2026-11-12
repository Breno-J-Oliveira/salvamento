# Avaliação prática para apresentação

As novas candidaturas recebem dossiês SOC ou AppSec com três entregas: investigação, decisão baseada nas evidências e parecer final. Os dossiês incluem identificadores correlacionáveis, atividade operacional legítima, observações ambíguas e informações ausentes. Os textos não prescrevem a vulnerabilidade ou a contenção esperada. A rubrica pública explica os critérios de revisão, sem fornecer a solução.

Cada avaliação iniciada guarda os briefings nas tabelas relacionais existentes. Alterações futuras no conteúdo não reescrevem o dossiê nem as respostas de uma candidatura já iniciada. A gravação de cada etapa continua definitiva e ordenada; o produto informa isso antes do envio. A quantidade de caracteres valida o formato e não decide mérito, nota ou contratação.

## Console de investigação

O laboratório final apresenta uma captura sintética somente de leitura: visão geral, acessos, eventos, processos, registro de mudanças e conexões. Há atividade legítima de backup, sondagem sem sucesso e uma sequência de exportações correlacionável pela identidade e pelos identificadores. O endereço associado à resposta objetiva continua derivado da semente da instância para compatibilidade com a validação da plataforma. A semente não é exibida nos endpoints.

Para atualizar a imagem: `docker build -t cti-lab/incident-01 challenges/incident-01`. Instâncias já abertas mantêm a imagem anterior até serem encerradas e recriadas. Não encerrar ambientes de outras pessoas durante uma apresentação.

## Limites

- As capturas não executam um ataque em tempo real nem representam logs do computador hospedeiro.
- A identificação de um endereço, isoladamente, não comprova competência seletiva. A avaliação por candidatura exige justificativa, referências, hipóteses e revisão humana.
- O conteúdo-fonte é público. Para seleção com necessidade de sigilo, são necessários novos casos reservados, regras de supervisão e política de tentativas; não prometer resistência completa a fraude.
- O conjunto é adequado para demonstração local do processo. Não equivale a homologação de produção ou aceite da empresa.

## Verificação

Testes de `tests/test_selection.py` cobrem titularidade, sequência, envio final, proteção contra sobrescrita, snapshots e isolamento do treino. `tests/test_incident_lab.py` cobre rotas somente de leitura, correlação entre fontes, variação de semente e ausência da semente nas respostas. A execução real do Docker deve ser registrada separadamente pela integração final.

Execução desta revisão: `unittest discover -s tests -p test_selection.py` concluiu 7/7 testes aprovados; `unittest discover -s tests -p test_incident_lab.py` concluiu 4/4 aprovados. Compilação Python e `git diff --check` passaram. Bancos temporários foram criados no D:, sem uso do banco real.
