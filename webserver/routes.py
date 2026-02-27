from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
import os
from werkzeug.utils import secure_filename
from config import PENDING_DIR, MOBILE_APP_TOKEN
import uuid

app = Flask(__name__)
# Chave secreta para flash messages no Flask
app.secret_key = "SMARTINVOICE_FLASK_SECRET_KEY"

# Configuração de uploads
app.config['UPLOAD_FOLDER'] = PENDING_DIR
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Máximo 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    # Middleware simples de segurança baseado no token na query string
    token = request.args.get('token')
    if token != MOBILE_APP_TOKEN:
        return "Acesso Negado. Utilize o link ou código QR disponibilizado no SmartInvoice.", 403
        
    return render_template('upload.html', token=token)

@app.route('/upload', methods=['POST'])
def upload_file():
    token = request.form.get('token')
    if token != MOBILE_APP_TOKEN:
        return "Acesso Negado.", 403
        
    if 'file' not in request.files:
        flash('Nenhum ficheiro selecionado')
        return redirect(url_for('index', token=token))
        
    file = request.files['file']
    if file.filename == '':
        flash('Nenhum ficheiro selecionado')
        return redirect(url_for('index', token=token))
        
    if file and allowed_file(file.filename):
        # Gera nome único para evitar sobreposições
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"mobile_upload_{uuid.uuid4().hex[:8]}.{ext}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        flash('Fatura enviada com sucesso!')
        return redirect(url_for('index', token=token))
        
    flash('Tipo de ficheiro não permitido.')
    return redirect(url_for('index', token=token))

@app.route('/api/update', methods=['GET'])
def get_update_info():
    """Retorna informação de atualização simulada. Num cenário real, isto estaria num servidor remoto"""
    response_data = {
        "latest_version": "1.1.0", # Hardcoded fake latest version to force an update prompt during testing
        "download_url": "https://example.com/download/smartinvoice_v1.1.0.exe",
        "release_notes": "Adicionada nova importação via API VIES.\nMelhoria de Performance no OCR das Faturas em PDF."
    }
    return jsonify(response_data), 200
