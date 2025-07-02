from flask import Flask, request, render_template, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename

from extractor import extrair_transacoes
from parser import processar_bloco_transacao
import datetime

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'super-secret-key'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_fetch_request():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        msg = "❌ Nenhum arquivo enviado."
        if is_fetch_request():
            return msg, 400
        flash(msg)
        return redirect(url_for('index'))

    file = request.files['file']
    senha = request.form.get("senha", "")
    
    if file.filename == '':
        msg = "❌ Nome de arquivo vazio."
        if is_fetch_request():
            return msg, 400
        flash(msg)
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        caminho_pdf = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(caminho_pdf)

        ano = datetime.datetime.now().year
        resultado = extrair_transacoes(caminho_pdf, ano, senha, processar_bloco_transacao)

        if "erro" in resultado:
            erro = resultado["erro"]
            msg = {
                "senha_incorreta": "❌ Senha incorreta do PDF.",
                "erro_leitura_pdf": "❌ Erro ao ler o arquivo PDF.",
                "erro_interno": "❌ Erro interno ou senha incorreta do PDF.",
                "nenhuma_transacao": "⚠️ Nenhuma transação encontrada no PDF."
            }.get(erro, "❌ Erro desconhecido.")

            if is_fetch_request():
                return msg, 400
            flash(msg)
            return redirect(url_for('index'))

        transacoes = resultado["dados"]
        qtd_pagamentos = sum(1 for t in transacoes if t["Valor"] < 0)
        qtd_compras = sum(1 for t in transacoes if t["Valor"] > 0)
        total = sum(t["Valor"] for t in transacoes)

        return render_template('partials/resumo.html',
                               transacoes=transacoes,
                               qtd_compras=qtd_compras,
                               qtd_pagamentos=qtd_pagamentos,
                               total=total)

    msg = "❌ Arquivo inválido. Envie apenas arquivos PDF."
    if is_fetch_request():
        return msg, 400
    flash(msg)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
