"""Desafio educacional de descoberta de arquivo. Nunca publicar na internet."""
import os
from flask import Flask, Response

app = Flask(__name__)
FLAG = os.environ["FLAG"]

@app.route("/health")
def health():
    return {"status": "ok"}

@app.route("/")
def index():
    return """<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Intranet CTI</title>
<style>body{background:#0f131c;color:#eee;font:16px system-ui;max-width:760px;margin:12vh auto;padding:24px}h1{color:#ddb7ff}small{color:#aaa}</style>
<small>CTI · LABORATÓRIO DE TREINAMENTO</small><h1>Intranet interna</h1>
<p>Portal de documentos da equipe. A migração do arquivo interno está em andamento.</p>
<p>Nada de interessante por aqui... ou será?</p></html>"""

@app.route("/robots.txt")
def robots():
    return Response("User-agent: *\nDisallow: /backup-interno\n", mimetype="text/plain")

@app.route("/backup-interno")
def backup():
    return Response(f"FLAG: {FLAG}", mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
