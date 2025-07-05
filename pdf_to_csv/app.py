from flask import Flask, request, render_template, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename
import datetime
import requests
from pdf_to_csv.extractor import extrair_transacoes
from pdf_to_csv.converter import salvar_csv
from pdf_to_csv.parser import processar_bloco_transacao

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'csv'}
ARQUIVO_SAIDA_CSV = "fatura_processada.csv"
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

if not N8N_WEBHOOK_URL:
    raise ValueError("A variável de ambiente N8N_WEBHOOK_URL não está definida. "
                     "Por favor, defina-a no seu docker-compose.yml ou ambiente de execução.")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.getenv("FLASK_SECRET_KEY", "sua-chave-secreta-de-desenvolvimento")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_fetch_request():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def send_csv_to_n8n(csv_filepath, bank_type, original_filename):
    """
    Envia o conteúdo de um arquivo CSV para um webhook do n8n.
    """
    try:
        with open(csv_filepath, 'rb') as f: 
            files = {
                'file': (os.path.basename(csv_filepath), f, 'text/csv'),
                'bank_type': (None, bank_type),
                'original_filename': (None, original_filename) 
            }

            response = requests.post(N8N_WEBHOOK_URL, files=files) 
            response.raise_for_status()

            print(f"✅ Arquivo CSV enviado com sucesso para o n8n. Status: {response.status_code}")
            print(f"Resposta do n8n: {response.text}")
            return {"success": True, "message": "CSV enviado para o n8n com sucesso!"}
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar CSV para o n8n: {e}")
        return {"success": False, "message": f"Erro ao enviar CSV para o n8n: {e}"}
    except Exception as e:
        print(f"❌ Erro inesperado ao processar o envio para o n8n: {e}")
        return {"success": False, "message": f"Erro inesperado ao enviar para o n8n: {e}"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file_type = request.form.get('file_type') 
    bank_type = request.form.get('bank_type')
    senha = request.form.get("senha", "") 

    if 'file' not in request.files:
        msg = "❌ Nenhum arquivo enviado."
        if is_fetch_request():
            return msg, 400
        flash(msg)
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        msg = "❌ Nome de arquivo vazio."
        if is_fetch_request():
            return msg, 400
        flash(msg)
        return redirect(url_for('index'))

    original_filename = secure_filename(file.filename)
    caminho_arquivo_recebido = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
    file.save(caminho_arquivo_recebido)

    csv_to_send_path = None
    
    if file_type == 'pdf':
        if file and allowed_file(file.filename):
            ano = datetime.datetime.now().year
            resultado = extrair_transacoes(caminho_arquivo_recebido, ano, senha, processar_bloco_transacao)

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
            
            transacoes = resultado.get("dados", [])

            if transacoes:
                qtd_compras, qtd_pagamentos = salvar_csv(transacoes, ARQUIVO_SAIDA_CSV)
                csv_to_send_path = ARQUIVO_SAIDA_CSV # O CSV a ser enviado é o gerado
                print(f"\n✅ Sucesso! Transações salvas em '{ARQUIVO_SAIDA_CSV}'")
                print(f"📊 {qtd_compras} compras | {qtd_pagamentos} pagamentos/créditos")

                total = sum(t["Valor"] for t in transacoes)

                n8n_result = send_csv_to_n8n(csv_to_send_path, bank_type, original_filename)
                
                if not n8n_result["success"]:
                    msg = f"✅ PDF processado, mas: {n8n_result['message']}"
                    if is_fetch_request():
                        return msg, 200 
                    flash(msg, 'warning')
                    return redirect(url_for('index'))

                msg = f"✅ PDF processado com sucesso! {qtd_compras} compras e {qtd_pagamentos} pagamentos/créditos. Enviado para n8n."
                if is_fetch_request():
                    return msg, 200
                flash(msg, 'success')
                return redirect(url_for('index'))

            else:
                msg = "⚠️ Nenhuma transação encontrada. Verifique o PDF e a senha."
                if is_fetch_request():
                    return msg, 400
                flash(msg, 'warning')
                return redirect(url_for('index'))
        else:
            msg = "❌ Arquivo inválido para o tipo PDF. Envie apenas arquivos PDF."
            if is_fetch_request():
                return msg, 400
            flash(msg)
            return redirect(url_for('index'))

    elif file_type == 'csv':
        if file and original_filename.lower().endswith('.csv'):
            csv_to_send_path = caminho_arquivo_recebido             
            n8n_result = send_csv_to_n8n(csv_to_send_path, bank_type, original_filename)
            
            if n8n_result["success"]:
                msg = f"✅ Arquivo CSV '{original_filename}' recebido e enviado para o n8n com sucesso!"
                if is_fetch_request():
                    return msg, 200
                flash(msg, 'success')
                return redirect(url_for('index'))
            else:
                msg = f"❌ Erro ao enviar CSV '{original_filename}' para o n8n: {n8n_result['message']}"
                if is_fetch_request():
                    return msg, 400
                flash(msg, 'error')
                return redirect(url_for('index'))
        else:
            msg = "❌ Arquivo inválido para o tipo CSV. Envie apenas arquivos CSV."
            if is_fetch_request():
                return msg, 400
            flash(msg)
            return redirect(url_for('index'))

    else:
        msg = "❌ Tipo de arquivo não suportado."
        if is_fetch_request():
            return msg, 400
        flash(msg)
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)