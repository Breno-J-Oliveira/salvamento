> Ensaio integrado e correções mais recentes: [RETOMADA-VERIFICADA-20261112.md](RETOMADA-VERIFICADA-20261112.md). As anotações abaixo preservam o histórico e os limites da primeira integração.

## Rodada local de candidatos

Neste computador, o runtime privado está em `D:/purple-talent-runtime`. Para abrir uma rodada depois de ligar o PC, execute cada comando em um terminal PowerShell na raiz do projeto. Se a aplicação ou a ponte já estiverem rodando com este banco, aproveite os processos existentes.

```powershell
.\scripts\run_local.ps1 -Port 5000
.\.venv\Scripts\python.exe scripts/lab_tls_bridge.py --cert-file D:/purple-talent-runtime/bridge.crt --key-file D:/purple-talent-runtime/bridge.key --app-port 5000
.\.venv\Scripts\python.exe scripts/rotate_local_vm.py --database lab.db --runtime D:/purple-talent-runtime --count 2
```

O último comando agenda **duas VMs novas**, uma por vez. Se já houver uma máquina disponível ou ocupada, ele aguarda o encerramento antes de criar a primeira da rodada. Cada nova máquina recebe disco, credencial e cadastro próprios. O candidato entra em `/remote-labs`, atualiza a disponibilidade e inicia a sessão. Pode sair da página e usar **Retomar investigação** até o término do prazo. A próxima VM leva alguns minutos para iniciar. Mantenha os três processos abertos durante a rodada.

O operador para ao atingir a quantidade pedida ou ao identificar falha. Uma segunda execução para o mesmo banco é recusada. Para uma VM da rodada, 15 minutos sem primeiro contato ou três minutos sem contato após a conexão interrompem a operação. Se uma máquina preexistente ficar sem contato, inspecione seu supervisor antes de abrir outra rodada. Os artefatos privados permanecem no disco para a equipe aplicar sua política de retenção.

Para um ensaio paralelo use outro banco DEMO, outra porta da aplicação e outra porta da ponte. Configure a ponte com `--port` e `--app-port`, e passe a mesma porta da ponte ao operador com `--bridge-port`. O agente dentro do convidado continua usando o endereço privado e o certificado do runtime.

## Caminho local com QEMU portátil

O runtime usa QEMU portátil e Ubuntu 24.04 mínimo. Os exemplos de preparação manual abaixo usam o diretório padrão `.runtime/local-vm`. A imagem foi obtida da Canonical e o pacote Windows da fonte indicada pelo projeto QEMU. Ambos foram conferidos contra os hashes publicados. A configuração atual usa emulação TCG e o boot pode levar vários minutos.

Com os assets verificados já preparados neste PC, use o Python da `.venv` para iniciar `scripts/lab_tls_bridge.py --cert-file .runtime/local-vm/bridge.crt --key-file .runtime/local-vm/bridge.key --app-port 5000`. Em seguida execute `scripts/prepare_local_vm.py --database lab.db`, salve o JSON retornado em um arquivo privado e passe esse arquivo para `scripts/run_local_vm.py --metadata CAMINHO-DO-JSON`. O arquivo JSON contém caminhos e ID, sem o token. Para demonstrar com a base fictícia, use o banco de demonstração e a ponte com app-port5057.

A ponte e o supervisor devem permanecer em execução. O supervisor encerra a VM após aposentadoria ou por reserva de disco. O próximo uso exige novo overlay/seed/token. Credenciais e ISO pertencem ao operador e nunca entram no Git. O certificado local tem validade30dias e deve ser renovado com a VM correspondente antes de expirar. Esta preparação local não publica o servidor na internet.

Fontes [QEMU Windows](https://www.qemu.org/download/#windows) e [Ubuntu mínimo](https://cloud-images.ubuntu.com/minimal/releases/noble/release/).

---

# Operação dos laboratórios acompanhados

## Estado da implementação

Primeira fatia local implementada em 12/11/2026. A entrada é `/remote-labs`, com sessões, terminal por comando e observação pelo mentor. O agente executa dentro de uma VM Linux preparada pela equipe. Alocar uma máquina disponível é a operação atual do botão iniciar. Criar, desligar e excluir VMs pelo VirtualBox continua no plano do `claude.md`.

Infraestrutura informada pelo usuário: computador Windows do SENAI semelhante ao atual. Este host tem 15,75 GB de RAM e 5,23 GB livres no C:. VirtualBox e VM Linux estão ausentes. Reservar espaço adicional no servidor ou usar disco dedicado antes de preparar a imagem. Como estimativa inicial de planejamento, separar 1–2 GB de RAM e um disco virtual de 12 GB para uma VM pequena, com espaço físico para sistema e alterações. Medir o consumo real antes de aumentar concorrência.

## Preparação da VM pela equipe

Procedimento ainda precisa ser executado e homologado em VM Linux. A instalação no computador institucional depende da equipe responsável pelo equipamento.

1. Instalar/configurar VirtualBox no Windows e preparar uma VM Linux com Python 3 e systemd254 ou superior, como Ubuntu24.04. O agente verifica a versão antes de conectar. Manter plataforma e banco de contas fora da VM vulnerável. Desativar pastas compartilhadas, área de transferência compartilhada e arrastar/soltar.
2. Usar somente arquivos fictícios e serviços de treinamento. Configurar firewall da VM/rede para impedir acesso à rede institucional, ao host e às outras sessões. NAT, sozinho, permite conexões de saída e precisa ser complementado por essa política. Liberar a saída necessária do agente para a plataforma HTTPS e resolução DNS controlada.
3. Criar uma conta dedicada regular, com UID e GID a partir de 1000, grupo privado com o mesmo nome e sem grupos suplementares ou sudo. O supervisor é root e guarda a credencial. Cada comando roda como a conta dedicada com NoNewPrivileges, capabilities vazias e cgroup systemd próprio.
4. Instalar `scripts/lab_agent.py` em `/opt/purple-agent/lab_agent.py`, propriedade root, sem permissão de escrita para a conta do laboratório. Guardar o token em `/etc/purple-agent/token`, root:root, modo0600, diretório root sem escrita por outros.

Exemplo de preparação dentro da VM nova, pela administração Linux:

```sh
sudo useradd --create-home --user-group --shell /bin/bash purplelab
sudo install -d -o purplelab -g purplelab -m 700 /srv/purple-lab
sudo install -d -o root -g root -m 700 /etc/purple-agent
sudo install -d -o root -g root -m 755 /opt/purple-agent
```

Caso inicial sugerido, com arquivos sintéticos `access.log`, `plantao.txt` e `chamado.txt`, colocados pela equipe em `/srv/purple-lab`, propriedade purplelab. Um comando como `cat access.log` consulta arquivos reais da VM. O template deve ser salvo limpo ANTES de receber credencial individual. Cada clone recebe um cadastro e token próprios.

## Cadastrar um executor

Executar na pasta da plataforma, usando o Python da `.venv`. O banco deve existir e o arquivo de token de destino deve ser novo. O diretório escolhido precisa ser privado. No Windows, revisar as ACLs para que somente o operador e o serviço autorizado possam ler o arquivo. O código aplica modo0600 ao criar em Linux, mas isso não configura ACLs do Windows.

```powershell
& 'C:\Users\Dev_2o_Ano\Desktop\desafio-de-ideias\.venv\Scripts\python.exe' scripts/register_lab_machine.py --database lab.db --name 'SENAI VM 01' --token-file 'C:\CAMINHO-PRIVADO\vm01.token'
```

`CAMINHO-PRIVADO` é placeholder. O comando gera a credencial em arquivo e imprime somente identificação/caminho. O banco guarda SHA256 do token. Transferir o arquivo por canal administrativo seguro para a VM e aplicar root:root0600. Nunca colocar a credencial no workspace, no template compartilhado, na linha de comando ou no Git. Uma queda entre criar o arquivo e inserir no banco pode deixar arquivo órfão. Verificar o cadastro antes de tentar novamente com outro destino novo.

## Iniciar o agente Linux

Com o arquivo instalado e o site HTTPS configurado:

```sh
sudo python3 /opt/purple-agent/lab_agent.py \
  --server https://DOMINIO-DA-PLATAFORMA \
  --token-file /etc/purple-agent/token \
  --workspace /srv/purple-lab \
  --run-as purplelab \
  --isolated-lab
```

`DOMINIO-DA-PLATAFORMA` é placeholder. O agente recusa Windows, usuário executor privilegiado, grupo inadequado, ausência de systemd e HTTP externo. A opção `--isolated-lab` registra uma confirmação do operador, sem detectar ou criar uma VM. `--allow-local-http` é exclusivo de QA loopback na mesma máquina. O agente usa conexão de saída, recusa redirects e valida TLS. A expansão de variáveis pelo systemd é desabilitada para que o shell receba o comando original. Essa opção requer systemd254 ou superior, conforme [manual oficial](https://www.freedesktop.org/software/systemd/man/latest/systemd-run.html).

O site atual aceita hosts locais. Para publicar, configurar hosts permitidos no objeto Flask e servidor WSGI de produção com HTTPS. Configurar proxy confiável e esquema/origem corretamente, testar CSRF e fechar acesso direto ao backend. Essas tarefas ainda não foram executadas. O servidor de desenvolvimento atual fica em loopback e serve à validação local.

## Uso e limites

- Participante abre `/remote-labs`, confirma ciência do acompanhamento e inicia. Uma máquina conectada há menos de30segundos é reservada exclusivamente. Uma sessão ativa por participante, duração30minutos.
- Mentor abre a mesma entrada e escolhe Acompanhar. Comandos e resultados são visíveis, com anotações privadas. Todos os mentores atuais compartilham esse acesso. Separação por avaliador/organização é trabalho posterior.
- Cada comando abre um shell independente, com até25segundos,256MB,64tarefas e100% de uma CPU no cgroup. Limite de200comandos/sessão e16KB de saída capturada por comando. A saída aparece após o término. Editor interativo, PTY, desktop e captura de teclas ficam para outra etapa.
- A fila entrega cada comando uma vez. Perda de resposta pode deixar um comando como interrompido com resultado desconhecido. Consultar o histórico antes de decidir enviar outro comando, especialmente se alterar arquivos.
- Encerrar bloqueia novos comandos e marca a máquina como retirada de uso. Um comando que já executa pode continuar por até25segundos. O cgroup limita os processos do comando. A VM permanece ligada até a equipe desligar e recriar externamente.
- Recriar a VM limpa e registrar novo token antes de atender outra pessoa. O token anterior recebe estado retired e permanece sem novas tarefas. Fechar a página não encerra a sessão. Ao perder rede, o agente preserva o resultado em memória para reenviar sem repetir o comando. Reiniciar o agente pode perder esse resultado.
- Acompanhamento cobre somente comandos enviados pela interface. Acesso externo SSH/RDP e atividades de outros canais exigem auditoria própria. Histórico pode conter dados sensíveis: usar fixtures e restringir o acesso. Política e exclusão por retenção ainda precisam ser definidas antes de uso real.

## Verificação e recuperação

Testes Python usam bancos temporários e os testes de navegador têm servidor exclusivo em5071 com respostas sintéticas. Nunca conectar esse executor de QA ao banco da equipe. Os testes Linux reais do agente são opcionais e devem rodar apenas numa VM descartável. Backups em `output/qa` são ignorados pelo Git.

Se um agente ficar offline, não liberar sua máquina para outra pessoa. Verificar conectividade, serviço e token por canal administrativo. Se uma execução ficou interrompida, não presumir que suas alterações foram revertidas. Para voltar à interface anterior, reverter as alterações de código após backup e manter as tabelas novas preservadas. As migrações desta fatia adicionam tabelas e índices sem remover estruturas existentes.
