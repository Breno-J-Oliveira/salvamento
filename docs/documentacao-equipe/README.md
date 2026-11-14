# PURPLE TALENT — Plataforma de Cibersegurança e Recrutamento de Talentos

<p align="center">
  <img src="https://img.shields.io/badge/STATUS-CONCLUÍDO-7C3AED?style=for-the-badge" />
  <img src="https://img.shields.io/badge/VERSÃO-1.0-6D28D9?style=for-the-badge" />
  <img src="https://img.shields.io/badge/PYTHON-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FLASK-000000?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLITE-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/CYBERSECURITY-581C87?style=for-the-badge" />
</p>

---

## ÍNDICE

<div align="center">

[![SOBRE](https://img.shields.io/badge/SOBRE%20O%20PROJETO-581C87?style=for-the-badge)](#sobre-o-projeto)
[![OBJETIVO](https://img.shields.io/badge/OBJETIVO-581C87?style=for-the-badge)](#objetivo)
[![PROBLEMA](https://img.shields.io/badge/PROBLEMA-581C87?style=for-the-badge)](#problema-identificado)
[![SOLUÇÃO](https://img.shields.io/badge/SOLUÇÃO-581C87?style=for-the-badge)](#solução-proposta)
[![FUNCIONALIDADES](https://img.shields.io/badge/FUNCIONALIDADES-581C87?style=for-the-badge)](#funcionalidades)
[![CTF](https://img.shields.io/badge/CTF%20PURPLE%20TEAM-581C87?style=for-the-badge)](#desafio-ctf-e-purple-team)
[![USUÁRIOS](https://img.shields.io/badge/USUÁRIOS-581C87?style=for-the-badge)](#perfis-de-usuário)
[![TECNOLOGIAS](https://img.shields.io/badge/TECNOLOGIAS-581C87?style=for-the-badge)](#tecnologias-utilizadas)
[![ARQUITETURA](https://img.shields.io/badge/ARQUITETURA-581C87?style=for-the-badge)](#arquitetura-do-sistema)
[![BANCO](https://img.shields.io/badge/BANCO%20DE%20DADOS-581C87?style=for-the-badge)](#banco-de-dados)
[![SEGURANÇA](https://img.shields.io/badge/SEGURANÇA-581C87?style=for-the-badge)](#segurança)
[![INTERFACE](https://img.shields.io/badge/INTERFACE-581C87?style=for-the-badge)](#telas-da-plataforma)
[![PROTÓTIPO](https://img.shields.io/badge/PROTÓTIPO-581C87?style=for-the-badge)](#protótipo)
[![EXECUÇÃO](https://img.shields.io/badge/EXECUÇÃO-581C87?style=for-the-badge)](#instalação-e-execução)
[![EQUIPE](https://img.shields.io/badge/EQUIPE-581C87?style=for-the-badge)](#equipe)
[![CÓDIGO](https://img.shields.io/badge/VISUALIZAR%20CÓDIGO-7C3AED?style=for-the-badge)](#visualizar-código)

</div>

---

## SOBRE O PROJETO

O **Purple Talent** é uma plataforma web desenvolvida como parte do Projeto Saga SENAI, com o objetivo de unir **cibersegurança, desenvolvimento de habilidades técnicas e recrutamento de novos talentos**.

A solução utiliza desafios no formato **Capture The Flag (CTF)**, estruturados a partir da metodologia Purple Team, para proporcionar experiências práticas de ataque e defesa em ambientes controlados.

A plataforma foi desenvolvida para atender às necessidades da empresa parceira **CTI**, oferecendo uma alternativa aos processos seletivos tradicionais, permitindo que empresas identifiquem profissionais por meio de suas habilidades práticas, capacidade de resolução de problemas e trabalho em equipe.

Com o lema:

> **Prática para aprender. Evidências para conversar.**

O Purple Talent transforma o desempenho dos participantes em informações que podem ser utilizadas durante processos de recrutamento e seleção.

A plataforma reúne recursos de treinamento, desafios técnicos, acompanhamento de candidaturas, avaliação de competências e gerenciamento de processos seletivos em um único ambiente.

---

## OBJETIVO

O principal objetivo do Purple Talent é desenvolver uma plataforma capaz de conectar estudantes e profissionais iniciantes às oportunidades do mercado de cibersegurança, utilizando avaliações práticas como diferencial no recrutamento.

A solução busca:

- Desenvolver habilidades técnicas em segurança da informação.
- Proporcionar experiências práticas de ataque e defesa.
- Identificar talentos por meio de desafios CTF.
- Facilitar a avaliação de candidatos em processos seletivos.
- Gerar evidências sobre as competências demonstradas pelos participantes.
- Incentivar o pensamento crítico e a resolução de problemas.
- Promover o trabalho em equipe e a colaboração.
- Aproximar estudantes das oportunidades profissionais.

---

## PROBLEMA IDENTIFICADO

Os processos seletivos tradicionais apresentam dificuldades para identificar profissionais que realmente possuem conhecimentos práticos em cibersegurança.

A análise de currículos e entrevistas convencionais nem sempre permite verificar se um candidato consegue identificar vulnerabilidades, analisar registros de sistemas, responder a incidentes ou solucionar problemas técnicos.

Entre os principais desafios identificados estão:

- Dificuldade de comprovar habilidades técnicas por meio de currículos.
- Processos seletivos demorados e com custos elevados.
- Subjetividade na avaliação dos candidatos.
- Falta de oportunidades para demonstrar conhecimentos práticos.
- Dificuldade de identificar talentos em início de carreira.
- Necessidade de avaliações técnicas mais completas.

A partir desse cenário, surgiu a proposta de utilizar desafios CTF como ferramenta de desenvolvimento e recrutamento.

---

## SOLUÇÃO PROPOSTA

O Purple Talent oferece um ambiente digital que conecta três áreas principais:

**Treinamento + Avaliação Técnica + Recrutamento**

A plataforma permite que os participantes encontrem oportunidades, realizem candidaturas, resolvam desafios de cibersegurança e acompanhem seu desempenho.

Ao mesmo tempo, equipes técnicas e profissionais de RH podem acompanhar os resultados, avaliar competências e consultar informações sobre os candidatos.

### Fluxo principal da plataforma

```text
       ACESSO À PLATAFORMA
                |
                v
        CADASTRO / LOGIN
                |
                v
       ESCOLHA DE OPORTUNIDADES
                |
                v
        REALIZAÇÃO DA CANDIDATURA
                |
                v
         DESAFIOS CTF
                |
                v
       SUBMISSÃO DE FLAGS
                |
                v
      REGISTRO DE DESEMPENHO
                |
                v
       AVALIAÇÃO DE COMPETÊNCIAS
                |
                v
       RANKING E TALENT POOL
                |
                v
       ANÁLISE PELO RECRUTAMENTO
```

---

## FUNCIONALIDADES

A plataforma foi desenvolvida com diferentes módulos, organizados para atender às necessidades dos participantes, da equipe de mentoria e do RH.

### 1. Vagas e oportunidades

Área destinada à apresentação das oportunidades profissionais disponíveis.

Funcionalidades:

- Listagem de vagas.
- Pesquisa por cargo, empresa, palavra-chave ou local.
- Filtros por área de atuação.
- Filtros por modalidade de trabalho.
- Identificação das inscrições disponíveis.
- Informações resumidas sobre cada oportunidade.

### 2. Detalhes da vaga

Apresenta informações completas sobre a oportunidade selecionada.

Inclui:

- Descrição da vaga.
- Nível profissional.
- Modalidade de trabalho.
- Localização.
- Prazo de inscrição.
- Orientações sobre as próximas etapas.
- Processo de candidatura.

### 3. Formulário de candidatura

Permite que o participante envie suas informações para concorrer a uma oportunidade.

Funcionalidades:

- Formulários personalizados para cada vaga.
- Perguntas abertas.
- Questões de múltipla escolha.
- Salvamento de respostas como rascunho.
- Recuperação de formulários não finalizados.
- Revisão das informações antes do envio.
- Proteção contra envios duplicados.

### 4. Minhas candidaturas

Área destinada ao acompanhamento das candidaturas realizadas.

Permite visualizar:

- Vagas para as quais o participante se candidatou.
- Etapa atual do processo seletivo.
- Datas e prazos.
- Situação da candidatura.
- Feedback disponibilizado pela equipe.

### 5. Catálogo de desafios CTF

Disponibiliza desafios práticos de cibersegurança para o desenvolvimento e avaliação das habilidades técnicas.

Entre as categorias de desafios estão:

- Criptografia.
- Segurança Web.
- Análise de logs.
- Identificação de vulnerabilidades.
- Investigação de incidentes.
- Configuração segura de ambientes.

Cada desafio apresenta informações sobre sua categoria, pontuação, modalidade Red Team ou Blue Team e instruções para realização.

### 6. Submissão de flags

Permite que os participantes enviem as respostas encontradas durante os desafios.

Funcionalidades:

- Campo para envio da flag.
- Validação da resposta.
- Comparação utilizando hash SHA-256.
- Registro de pontuação.
- Controle de envios duplicados.
- Atualização do desempenho do participante.

### 7. Laboratórios virtuais

A plataforma disponibiliza ambientes isolados para a realização de atividades práticas de cibersegurança.

Os laboratórios utilizam máquinas virtuais gerenciadas pelo VirtualBox, permitindo que os participantes executem atividades em ambientes controlados.

Características:

- Criação de ambientes individuais.
- Isolamento entre participantes.
- Controle de instâncias ativas.
- Identificação de portas e desafios.
- Tempo de utilização limitado.
- Expiração automática dos ambientes.

### 8. Dossiê da candidatura

Reúne informações relevantes sobre o candidato em um único ambiente.

Apresenta:

- Dados da candidatura.
- Respostas dos formulários.
- Evidências das atividades realizadas.
- Desempenho nos desafios.
- Histórico de participação.
- Informações sobre competências demonstradas.

### 9. Rubrica por competência

Ferramenta utilizada pela equipe de mentoria para avaliar o desempenho dos participantes.

Permite analisar competências técnicas e comportamentais por meio de critérios padronizados.

Entre os aspectos avaliados estão:

- Conhecimento técnico.
- Capacidade de análise.
- Resolução de problemas.
- Pensamento crítico.
- Comunicação.
- Colaboração.
- Trabalho em equipe.

### 10. Parecer interno e feedback

Área destinada ao registro das avaliações realizadas pela equipe.

Permite separar informações internas do feedback que pode ser compartilhado com o participante.

Inclui:

- Registro de pareceres.
- Avaliações individuais.
- Correção automática de questões objetivas.
- Feedback para o candidato.
- Informações restritas à equipe autorizada.

### 11. Painel de processos seletivos

Área administrativa destinada ao gerenciamento das oportunidades.

Funcionalidades:

- Visualização do número de vagas.
- Acompanhamento de candidaturas.
- Identificação de formulários em rascunho.
- Consulta de avaliações pendentes.
- Criação de novas vagas.
- Edição de oportunidades.
- Publicação, pausa e encerramento de vagas.
- Gerenciamento de formulários personalizados.

### 12. Avaliação Purple Team

Painel destinado à equipe técnica e aos mentores.

Permite acompanhar:

- Quantidade de participantes.
- Equipes cadastradas.
- Desafios realizados.
- Pontuação individual e coletiva.
- Tentativas realizadas.
- Desempenho das equipes.
- Evidências das atividades.

### 13. Talent Pool e Ranking

Área responsável por apresentar a classificação dos participantes com base no desempenho obtido nos desafios.

Apresenta:

- Pontuação acumulada.
- Participantes classificados.
- Equipes.
- Quantidade de desafios resolvidos.
- Pesquisa por participante ou equipe.
- Informações para identificação de talentos.

O objetivo é facilitar a identificação de candidatos com maior domínio técnico e potencial profissional.

### 14. Gerenciamento de ambientes virtuais

Área administrativa destinada ao monitoramento dos laboratórios em funcionamento.

Permite:

- Consultar ambientes ativos.
- Identificar participantes conectados.
- Visualizar desafios associados.
- Acompanhar portas utilizadas.
- Consultar o tempo de expiração.
- Encerrar ambientes individualmente.
- Encerrar todas as instâncias.

---

## DESAFIO CTF E PURPLE TEAM

O projeto utiliza duas abordagens importantes da área de segurança da informação: Capture The Flag (CTF) e Purple Team.

### Capture The Flag (CTF)

O CTF é um formato de desafio utilizado em treinamentos e competições de cibersegurança.

Os participantes precisam identificar informações específicas, chamadas de *flags*, por meio da resolução de problemas técnicos.

A cada desafio concluído, o participante pode receber pontos, que são utilizados para acompanhar seu desempenho.

### Red Team

Representa o lado ofensivo da segurança da informação.

Os participantes atuam simulando ataques controlados, buscando identificar vulnerabilidades e explorar falhas em ambientes autorizados.

### Blue Team

Representa o lado defensivo da segurança da informação.

Os participantes trabalham na proteção dos sistemas, identificação de atividades suspeitas, análise de registros e aplicação de medidas de segurança.

### Purple Team

Integra as duas abordagens, incentivando a colaboração entre ataque e defesa.

O objetivo é desenvolver profissionais capazes de compreender diferentes perspectivas da segurança digital.

**Importante:** todas as atividades práticas devem ocorrer exclusivamente em ambientes isolados, autorizados e controlados.

---

## PERFIS DE USUÁRIO

A plataforma foi desenvolvida considerando três perfis principais.

### Candidato / Participante

Responsável por utilizar a plataforma para desenvolver habilidades e participar dos processos seletivos.

Pode:

- Consultar oportunidades.
- Realizar candidaturas.
- Resolver desafios CTF.
- Enviar flags.
- Utilizar laboratórios virtuais.
- Consultar seu desempenho.
- Acompanhar sua evolução.
- Visualizar feedbacks disponibilizados.

### Mentoria / Equipe Técnica

Responsável por acompanhar as atividades e avaliar o desempenho dos participantes.

Pode:

- Acompanhar equipes.
- Consultar desafios.
- Analisar pontuações.
- Avaliar competências.
- Registrar pareceres.
- Acompanhar evidências técnicas.
- Fornecer feedbacks.

### RH / Recrutamento

Responsável por administrar oportunidades e utilizar os resultados das avaliações como apoio aos processos seletivos.

Pode:

- Criar e gerenciar vagas.
- Consultar candidaturas.
- Visualizar dossiês.
- Consultar o ranking.
- Acompanhar o Talent Pool.
- Analisar informações dos candidatos.
- Consultar avaliações e feedbacks autorizados.

---

## TECNOLOGIAS UTILIZADAS

O desenvolvimento do Purple Talent utiliza tecnologias voltadas à construção de aplicações web, gerenciamento de dados, segurança e virtualização.

| Tecnologia | Aplicação no projeto |
|---|---|
| Python 3.12+ | Linguagem principal do back-end |
| Flask 3.1 | Framework para rotas e regras de negócio |
| SQLite | Banco de dados relacional |
| HTML5 | Estrutura das páginas |
| Jinja2 | Renderização dinâmica de páginas |
| CSS3 | Estilização e identidade visual |
| JavaScript | Interatividade da interface |
| VirtualBox | Criação e execução dos laboratórios virtuais |
| VBoxManage | Gerenciamento das máquinas virtuais |
| Vagrant | Organização dos ambientes virtuais |
| Figma | Criação dos protótipos e interfaces |
| Google Stitch | Apoio à criação das telas |
| Playwright | Testes automatizados de navegador |
| unittest | Testes automatizados em Python |
| PowerShell | Scripts de inicialização e gerenciamento |

### Python e Flask

Utilizados no desenvolvimento do back-end, responsáveis por:

- Gerenciamento de rotas.
- Regras de negócio.
- Autenticação por sessão.
- Processamento de formulários.
- Controle de permissões.
- Integração com o banco de dados.

### SQLite

Utilizado para armazenar informações relacionadas a:

- Usuários.
- Desafios.
- Submissões.
- Pontuações.
- Vagas.
- Candidaturas.
- Formulários.
- Rubricas.
- Histórico de atividades.

### HTML5, CSS3 e JavaScript

Responsáveis pela construção e apresentação das interfaces da plataforma.

O projeto utiliza páginas renderizadas pelo servidor com Jinja2, estilização própria e componentes interativos.

### VirtualBox e Vagrant

Utilizados na criação e no gerenciamento dos laboratórios virtuais, possibilitando a execução de desafios em ambientes isolados.

### Figma e Google Stitch

Ferramentas utilizadas no planejamento visual, criação de interfaces e desenvolvimento dos protótipos da plataforma.

---

## ARQUITETURA DO SISTEMA

A arquitetura do Purple Talent é organizada a partir da comunicação entre o navegador, o servidor Flask, o banco de dados SQLite e o módulo responsável pelos laboratórios virtuais.

### Funcionamento da arquitetura

```text
              USUÁRIO
                 |
                 v
             NAVEGADOR
                 |
                 v
          HTML / CSS / JS
                 |
                 v
          PYTHON + FLASK
                 |
        +--------+--------+
        |                 |
        v                 v
   BANCO SQLITE      REGRAS DE NEGÓCIO
        |                 |
        +--------+--------+
                 |
                 v
        MÓDULO DE LABORATÓRIOS
                 |
                 v
       VIRTUALBOX / VAGRANT
                 |
                 v
       AMBIENTES ISOLADOS
```

O Flask processa as solicitações realizadas pelo usuário, aplica as regras de negócio e realiza as operações necessárias no banco de dados.

O módulo de virtualização atua separadamente para criar e administrar os ambientes utilizados nos desafios práticos.

---

## BANCO DE DADOS

O projeto utiliza SQLite como sistema de gerenciamento de banco de dados.

A estrutura relacional permite organizar as informações da plataforma e estabelecer relacionamentos entre usuários, desafios, candidaturas, vagas e avaliações.

Entre as principais entidades estão:

- Usuários.
- Desafios.
- Submissões.
- Vagas.
- Candidaturas.
- Formulários.
- Respostas.
- Rubricas.
- Avaliações.
- Histórico.
- Ambientes virtuais.

O banco de dados permite manter registros das atividades realizadas e relacionar as informações necessárias para o acompanhamento dos participantes.

---

## SEGURANÇA

Por se tratar de uma plataforma voltada à cibersegurança, a proteção das informações e o isolamento dos ambientes são aspectos fundamentais do projeto.

Entre os mecanismos implementados estão:

- Autenticação por sessão.
- Controle de acesso às áreas restritas.
- Proteção CSRF.
- Utilização de hash SHA-256 para validação das flags.
- Separação entre informações internas e feedback compartilhado.
- Ambientes virtuais isolados.
- Dados fictícios para demonstração.
- Controle de expiração dos laboratórios.
- Registro de atividades.

A plataforma foi projetada para que os desafios sejam executados em ambientes controlados, sem interação com sistemas reais não autorizados.

---

## TELAS DA PLATAFORMA

A interface do Purple Talent foi desenvolvida para organizar as informações de maneira intuitiva, facilitando a navegação entre oportunidades, desafios, avaliações e processos seletivos.

### Principais telas desenvolvidas

| Tela | Descrição |
|---|---|
| Vagas | Apresentação das oportunidades disponíveis |
| Detalhes da vaga | Informações completas sobre a oportunidade |
| Candidatura | Formulário personalizado para inscrição |
| Minhas candidaturas | Acompanhamento dos processos seletivos |
| Catálogo CTF | Listagem dos desafios disponíveis |
| Submissão de flags | Envio e validação das respostas |
| Laboratórios | Acesso aos ambientes virtuais |
| Dossiê | Histórico e evidências do candidato |
| Rubrica | Avaliação das competências |
| Parecer e feedback | Registro das avaliações |
| Painel RH | Gerenciamento de processos seletivos |
| Painel de mentoria | Acompanhamento das equipes |
| Talent Pool | Classificação dos participantes |
| Ambientes virtuais | Monitoramento das instâncias |

---

## PROTÓTIPO

O protótipo foi desenvolvido durante a etapa de planejamento visual da plataforma, permitindo estruturar as principais telas, componentes e fluxos de navegação antes da implementação.

A identidade visual foi organizada para transmitir uma experiência tecnológica, moderna e relacionada ao universo da cibersegurança.

**Ferramentas utilizadas:**
- Figma.
- Google Stitch.

[![VISUALIZAR PROTÓTIPO](https://img.shields.io/badge/VISUALIZAR%20PROTÓTIPO-FIGMA-7C3AED?style=for-the-badge&logo=figma&logoColor=white)](https://www.figma.com/design/BagQgwirGZyDbrtzNpQkOA/Purple-Talent?node-id=0-1&t=Pzqw1EXMFYfU73FR-1)

---

## INSTALAÇÃO E EXECUÇÃO

Para executar o projeto localmente, é necessário preparar o ambiente com Python, Flask, SQLite e as ferramentas utilizadas para os laboratórios virtuais.

### Pré-requisitos

- Python 3.12 ou superior.
- Pip.
- Navegador atualizado.
- VirtualBox, para utilização dos laboratórios.
- Vagrant, conforme a configuração dos ambientes.

### 1. Clonar o repositório

```bash
git clone URL_DO_REPOSITORIO
```

### 2. Acessar a pasta

```bash
cd purple-talent
```

### 3. Criar ambiente virtual

```bash
python -m venv venv
```

### 4. Ativar o ambiente virtual

Windows:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

### 5. Instalar as dependências

Caso o projeto possua um arquivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 6. Executar a aplicação

Utilize o comando de inicialização definido no projeto. Caso a aplicação esteja configurada para execução pelo Flask:

```bash
flask --app app run --debug
```

Acesse o endereço local apresentado no terminal para visualizar a plataforma.

**Observação:** os nomes dos arquivos e o comando de inicialização devem corresponder à estrutura efetiva do projeto.

---

## RESULTADOS ALCANÇADOS

O desenvolvimento do Purple Talent resultou em uma plataforma que integra treinamento prático em cibersegurança e recrutamento baseado em evidências.

Entre as principais entregas estão:

- Desenvolvimento da plataforma web.
- Implementação de autenticação e controle de acesso.
- Catálogo de desafios CTF.
- Sistema de submissão e validação de flags.
- Sistema de pontuação e ranking.
- Gerenciamento de candidaturas.
- Painel administrativo de RH.
- Painel de avaliação da mentoria.
- Rubrica de competências.
- Dossiê dos candidatos.
- Feedback individual.
- Gerenciamento de laboratórios virtuais.
- Integração com máquinas virtuais isoladas.
- Testes automatizados.
- Documentação técnica do projeto.

A solução amplia as possibilidades de avaliação de profissionais em início de carreira, permitindo observar habilidades demonstradas em situações práticas.

---

## EQUIPE

Projeto desenvolvido pelos alunos da **Escola SENAI A. Jacob Lafer**, no âmbito do Projeto Saga SENAI.

| Integrante | Responsabilidade |
|---|---|
| Ana Carolina | Desenvolvimento |
| Breno José | Desenvolvimento |
| João Pedro Tomazini | Desenvolvimento |
| Leonardo Alves | Desenvolvimento |
| Nicolas Tukaze | Desenvolvimento |
| Paolla Veronêz | Product Owner |
| Rafaela Oliveira | Scrum Master |

---

## VISUALIZAR CÓDIGO

Acesse a pasta com os arquivos, códigos-fonte e materiais relacionados ao desenvolvimento do Purple Talent.

<p align="center">
  <a href="https://drive.google.com/drive/folders/1vQv-94xSYZmelZVAAGZU_H12GMoRu6JM?usp=sharing">
    <img src="https://img.shields.io/badge/VISUALIZAR%20CÓDIGO-ABRIR%20ARQUIVOS-7C3AED?style=for-the-badge&logo=googledrive&logoColor=white" />
  </a>
</p>

---

## CONSIDERAÇÕES FINAIS

O Purple Talent representa uma proposta de inovação na formação e identificação de profissionais de cibersegurança.

Ao integrar desafios CTF, metodologia Purple Team e processos de recrutamento, a plataforma proporciona uma experiência que vai além da avaliação tradicional por currículos.

O projeto demonstra como a tecnologia pode aproximar estudantes do mercado de trabalho, incentivando o desenvolvimento de competências técnicas, raciocínio lógico, colaboração e pensamento crítico.

**Purple Talent — Prática para aprender. Evidências para conversar.**

---

<p align="center">
  <strong>PROJETO SAGA SENAI — 2026</strong><br>
  Escola SENAI A. Jacob Lafer<br>
  Santo André — SP
</p>
