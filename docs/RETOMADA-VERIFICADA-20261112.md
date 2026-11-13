# Retomada verificada da versão com VM Linux

Base baixada de main do repositório Breno-J-Oliveira/salvamento: 123e10dcd54d951cf2ad26e94e65e290b53e3181. Esta etapa continua a direção de laboratórios remotos acompanhados, sem depender do Docker no percurso principal.

## Preservação

O checkout anterior permanece na branch codex/continue-salvamento. O trabalho novo usa codex/resume-linux-vm-20261112. Antes da atualização foi criada uma cópia SQLite verificada em diretório privado fora do repositório. Banco, chave, runtime e credenciais não são publicados.

## Correções e integração neste computador

- Launcher compatível com Windows PowerShell 5: a identificação de versão não depende de aspas internas em python -c, e a conferência da base demo foi movida para scripts/verify_demo.py, que só lê o arquivo e recusa base operacional, ausente ou sem marcador.
- Identificadores de URL acima do limite inteiro de SQLite retornam 404, em vez de lançar OverflowError em páginas corporativas e de desafios.
- Handshake TLS executado em worker com limite de conexões: cliente lento não bloqueia a recepção dos demais agentes. Rejeições pequenas descartam corpo de modo limitado, evitando resets comuns; corpos arbitrários não são consumidos.
- Runtime da VM pode ficar em outro disco com --runtime. Preparação valida assets antes de cadastrar executor, falhas aposentam o cadastro, supervisor usa reserva exclusiva e impede duas inicializações do mesmo metadata.
- Os dois testes Linux foram ajustados para workspace em /srv; PrivateTmp continua habilitado. Não foi enfraquecido o isolamento do agente.
- Teste de apresentação atualizado para o nome atual do link Laboratório acompanhado.

## Verificação realizada

- 240 casos Python atuais reconciliados por identificador: 235 aprovados no Windows e 2 testes systemd aprovados dentro da VM Linux; 3 condicionais Docker legado não executados. A primeira execução completa encontrou um reset da ponte e um timeout de preparação da demo sob carga. A ponte foi corrigida e seus 12 testes passaram; os 4 testes da demo passaram na repetição isolada. Não se afirma que houve uma única execução integral sem erros antes dessas correções.
- Novos testes: 11 de portabilidade/lifecycle, 3 de verificação da demo e 1 de limites de identificador. Logs de cobertura e resultados sintéticos ficam em D:/purple-talent-qa, fora do Git.
- Navegador: sistemas internos 10/10; apresentação 15/15; protocolo remoto com respostas sintéticas 7/7; recrutamento 18/18. Gestão de vagas 10/10. Com o ensaio real de 9 casos, totalizam 69 cenários de navegador, distinguindo protocolo sintético e VM real.
- Ensaio Linux real 9/9: reserva online; UID1100/grupo privado/QEMU; leitura real dos artefatos; testes systemd sem skips; token e cloud-init inacessíveis ao executor; bloqueio de host e internet; filho setsid removido com o cgroup; acompanhamento e observações privadas; encerramento com histórico e aposentadoria.
- A sessão real de QA consumiu uma VM descartável no banco DEMO, nunca a VM destinada ao participante do banco principal. Sua máquina terminou retired e o supervisor encerrou o processo.
- Compilação Python, pip check e git diff --check verificados.

Os três casos não executados são a integração antiga de duas instâncias Docker, o console Docker antigo e a condição que exige um host sem Docker instalado. Os testes de VM Linux não substituem esses casos nem uma auditoria independente.

## Runtime e operação

Os assets privados desta máquina estão em D:/purple-talent-runtime, com ACL restrita ao operador e SYSTEM. O manifesto público RUNTIME-VERIFICADO.json registra fontes e hashes: QEMU e Ubuntu conferidos também com os arquivos de checksum oficiais; 7-Zip conferido com digest da release oficial; pycdlib conferido com o hash da distribuição PyPI. Instaladores não foram executados: os binários foram extraídos. Nenhum driver, BIOS ou recurso de virtualização Windows foi alterado.

O ensaio usa emulação TCG e pode levar minutos para inicializar. O modo principal exige três processos: aplicação, ponte TLS e supervisor. Na retomada, verificar se já estão ativos antes de iniciar outros; o launcher recusa porta ocupada.

Exemplo para uma NOVA preparação, depois de conferir assets privados:

```powershell
.\scripts\run_local.ps1 -Port 5000
# Em outro terminal
.\.venv\Scripts\python.exe scripts/lab_tls_bridge.py --cert-file D:/purple-talent-runtime/bridge.crt --key-file D:/purple-talent-runtime/bridge.key --app-port 5000
# Criar metadata em arquivo privado UTF-8; não reutilizar sessão aposentada
.\.venv\Scripts\python.exe scripts/prepare_local_vm.py --runtime D:/purple-talent-runtime --database lab.db
.\.venv\Scripts\python.exe scripts/run_local_vm.py --runtime D:/purple-talent-runtime --metadata CAMINHO-PRIVADO-DO-METADATA
```

Certificados, chaves, tokens, imagens, seeds, overlays, metadata e logs privados não vêm no clone. A preparação não é um instalador automático de runtime e não cria um pool automaticamente pelo site. Preservar os limites e procedimentos de LABORATORIOS-REMOTOS.md e RETOMADA-OUTRA-MAQUINA.md.

## Próximo marco

Depois de confirmar o executor limpo no banco principal sem reservá-lo para QA, avançar a preparação/recriação operacional controlada. Criação pelo site, vários executores, terminal interativo e hospedagem HTTPS externa continuam pendentes. Não reutilizar um executor aposentado para outra pessoa e não confundir loopback local com publicação na internet.

## Estado deixado disponível

A aplicação principal está em http://127.0.0.1:5000 e a demonstração em http://127.0.0.1:5057. A ponte TLS foi direcionada ao principal5000 e um novo executor limpo foi preparado em lab.db. O heartbeat foi confirmado com idade inferior a30segundos, estado available e zero sessões no principal. A VM usada no ensaio anterior foi desligada e aposentada. Nenhum teste consumiu o novo executor destinado ao usuário.

Para começar, entrar como participante e abrir /remote-labs. A disponibilidade depende da aplicação, ponte e supervisor continuarem abertos. Ao encerrar a sessão, a máquina é aposentada; uma próxima pessoa exige nova preparação. Este registro é um checkpoint, não garantia de que processos continuem vivos após fechar o aplicativo ou reiniciar o computador.
