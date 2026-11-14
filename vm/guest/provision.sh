#!/bin/sh
set -eu
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q python3-flask
id ctf >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin ctf
rm -rf /opt/cti-lab && mkdir -p /opt/cti-lab
cp -r /tmp/challenges/web-01 /tmp/challenges/incident-01 /opt/cti-lab/
rm -f /opt/cti-lab/*/Dockerfile
install -m 0755 /tmp/run.sh /opt/cti-lab/run.sh
install -m 0644 /tmp/cti-lab.service /etc/systemd/system/cti-lab.service
chown -R root:root /opt/cti-lab && chmod -R go-w /opt/cti-lab
systemctl daemon-reload
systemctl enable cti-lab.service
# A VM base não deve guardar flag nem desafio próprios.
apt-get clean
