from flask import Flask, render_template, request, redirect, url_for
import csv
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

responsaveis_emails = {
    "Gabriel": "gabriel@it4d.com.br",
    "Gabriela": "gabriela.cleim@it4d.com.br",
    "Matheus": "matheus@it4d.com.br",
    "David": "davidson123@it4d.com.br"
}

ARQUIVO = "bugs.csv"
CAMPOS = [
    "id", "data", "descricao", "passos", "esperado", "obtido",
    "ambiente", "status", "responsavel", "anexo", "sistema", "Obs"
]

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    bugs = carregar_bugs()

    termo = request.args.get("termo", "").lower()
    status = request.args.get("status", "")

    if termo:
        bugs = [b for b in bugs if termo in b["descricao"].lower()]



    if status:
        bugs = [b for b in bugs if b["status"] == status]

    return render_template("index.html", bugs=bugs)

def enviar_email(destinatario, assunto, mensagem, caminho_anexo=None):
    smtp_server = "smtp.office365.com"
    smtp_port = 587
    email_origem = "gustavo.cardena@it4d.com.br"
    senha = "G2a@1401"

    msg = MIMEMultipart()
    msg["From"] = email_origem
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.attach(MIMEText(mensagem, "plain"))

    if caminho_anexo:
        with open(caminho_anexo, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(caminho_anexo))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(caminho_anexo)}"'
            msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_origem, senha)
        server.send_message(msg)
        server.quit()
        print(f"E-mail enviado para {destinatario}")
    except Exception as e:
        print(f"Erro ao enviar e-mail para {destinatario}: {e}")

def carregar_bugs():
    try:
        with open(ARQUIVO, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []

def salvar_bugs(bugs):
    with open(ARQUIVO, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writeheader()
        writer.writerows(bugs)



@app.route("/adicionar", methods=["GET", "POST"])
def adicionar():
    if request.method == "POST":
        bugs = carregar_bugs()
        novo_bug = {
            "id": str(len(bugs) + 1),
            "data": datetime.now().strftime('%d/%m/%Y'),
            "descricao": request.form["descricao"],
            "passos": request.form["passos"],
            "esperado": request.form["esperado"],
            "obtido": request.form["obtido"],
            "ambiente": request.form["ambiente"],
            "Obs": request.form["Observação"],
            "status": "Novo",
            "responsavel": request.form["responsavel"],
            "anexo": "",
            "sistema": request.form.get("sistema", "")
        }

        caminho_anexo = None

        anexo = request.files.get("anexo")
        if anexo and anexo.filename:
            filename = secure_filename(anexo.filename)
            caminho_anexo = os.path.join(UPLOAD_FOLDER, filename)
            anexo.save(caminho_anexo)
            novo_bug["anexo"] = filename

        bugs.append(novo_bug)
        salvar_bugs(bugs)

        responsavel = novo_bug["responsavel"]
        email_destino = responsaveis_emails.get(responsavel)
        if email_destino:
            assunto = f"Novo Bug Atribuído"
            corpo = f"""Olá {responsavel},

Você recebeu um novo bug do guzin do QA:

Descrição: {novo_bug['descricao']}
Passos: {novo_bug['passos']}
Esperado: {novo_bug['esperado']}
Obtido: {novo_bug['obtido']}
Ambiente: {novo_bug['ambiente']}
Observação: {novo_bug['Obs']}

Por favor, verifique o sistema para mais detalhes.
"""
            enviar_email(email_destino, assunto, corpo, caminho_anexo)

        return redirect(url_for("index"))

    return render_template("adc.html", responsaveis=responsaveis_emails.keys())


@app.route("/editar/<id>", methods=["GET", "POST"])
def editar(id):
    bugs = carregar_bugs()
    bug = next((b for b in bugs if b["id"] == id), None)
    if not bug:
        return "Bug não encontrado", 404

    if request.method == "POST":
        bug["descricao"] = request.form["descricao"]
        bug["passos"] = request.form["passos"]
        bug["esperado"] = request.form["esperado"]
        bug["obtido"] = request.form["obtido"]
        bug["ambiente"] = request.form["ambiente"]
        bug["Obs"] = request.form["Observação"]
        bug["responsavel"] = request.form["responsavel"]
        salvar_bugs(bugs)

        return redirect(url_for("index"))

    return render_template("editar.html", bug=bug, responsaveis=responsaveis_emails.keys())

@app.route("/atualizar/<id>", methods=["GET", "POST"])
def atualizar(id):
    bugs = carregar_bugs()
    bug = next((b for b in bugs if b["id"] == id), None)
    if not bug:
        return "Bug não encontrado", 404

    if request.method == "POST":
        bug["status"] = request.form["status"]
        salvar_bugs(bugs)
        return redirect(url_for("index"))

    return render_template("atualizar.html", bug=bug)

@app.route("/excluir/<id>")
def excluir(id):
    bugs = carregar_bugs()
    bugs = [b for b in bugs if b["id"] != id]
    salvar_bugs(bugs)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
