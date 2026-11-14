#!/bin/sh
# Lê desafio e flag das guest properties (somente leitura para o convidado)
# e executa o desafio como usuário sem privilégios na porta 5000.
set -eu
prop() { VBoxControl --nologo guestproperty get "$1" 2>/dev/null | sed -n 's/^Value: //p'; }
for _ in $(seq 1 120); do
  CHALLENGE=$(prop /CTI/Challenge || true)
  FLAG=$(prop /CTI/Flag || true)
  [ -n "$CHALLENGE" ] && [ -n "$FLAG" ] && break
  sleep 1
done
case "${CHALLENGE:-}" in
  web-01|incident-01) ;;
  *) echo "desafio não configurado" >&2; exit 1 ;;
esac
export FLAG PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
cd "/opt/cti-lab/$CHALLENGE"
exec setpriv --reuid=ctf --regid=ctf --init-groups --no-new-privs python3 app.py
