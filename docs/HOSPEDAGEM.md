# Hospedagem do Purple Talent

Use um Web Service no Render com disco persistente. O disco tem custo e deve ser contratado de acordo com o plano escolhido. Execute somente uma instância para compartilhar o SQLite.

1. Conecte o GitHub e crie um Web Service para o repositório.
2. Use como build command: pip install -r requirements.txt
3. Use como start command: python scripts/start_production.py
4. Monte um disco persistente em /var/data.
5. Configure PURPLE_ENV=production, PERSISTENT_MOUNT=/var/data, LAB_DATABASE=/var/data/lab.db, SECRET_KEY com pelo menos 32 caracteres aleatórios, ALLOWED_HOSTS com o domínio sem protocolo, e MENTOR_PASSWORD com pelo menos 12 caracteres. PORT é fornecida pela plataforma.
6. Teste uma inscrição fictícia em um computador e a consulta do mentor em outro. Reinicie o serviço e verifique os registros. Teste backup e restauração em destino separado.

A conta inicial do mentor é mentor@cti.local. A senha de demonstração é recusada em produção. A versão recebida usa VirtualBox/Vagrant para VMs locais e essas rotas são bloqueadas na hospedagem até haver integração compatível. Antes de seleção real, revise a segurança, retenção e recuperação de dados. Algumas respostas dos desafios estão no código do repositório público e precisam ser substituídas para uma prova seletiva.

## Para a próxima IA

Valide a implantação real, proxy e domínio, sessões em computadores distintos, limites, persistência após reinício e redeploy, e restauração de backup. Implemente infraestrutura isolada de VMs antes de habilitar esses desafios em produção. Não publique bancos, chaves ou gabaritos.

Fontes: https://render.com/docs/disks e https://render.com/docs/deploy-flask
