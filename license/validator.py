import os
import json
import base64
import hmac
import hashlib
import datetime
from license.license_manager import get_machine_id

# ATENÇÃO: Na aplicação final o SECRET_KEY tem de ser igual ao do generator, mas ofuscado!
SECRET_KEY = b"SMARTINVOICE_SUPER_SECRET_KEY_2026_CHANGE_ME"
LICENSE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "license.key")

def is_license_valid():
    """Valida se a licença existe no computador, se a assinatura é válida e se não expirou."""
    if not os.path.exists(LICENSE_FILE):
        return False, "Licença não encontrada."
        
    try:
        with open(LICENSE_FILE, "r") as f:
            license_key = f.read().strip()
            
        if "." not in license_key:
            return False, "Formato de licença inválido."
            
        payload_b64, signature = license_key.split(".")
        
        # 1. Verifica Assinatura
        expected_signature = hmac.new(SECRET_KEY, payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return False, "A licença foi manipulada! Assinatura inválida."
            
        # 2. Descodifica o payload
        payload_str = base64.b64decode(payload_b64).decode()
        license_data = json.loads(payload_str)
        
        # 3. Verifica o Machine ID
        current_machine_id = get_machine_id()
        if license_data.get("machine_id") != current_machine_id:
            return False, f"Licença registada para outro computador."
            
        # 4. Verifica Data de Expiração
        expire_date_str = license_data.get("expires")
        expire_date = datetime.datetime.strptime(expire_date_str, "%Y-%m-%d")
        if datetime.datetime.utcnow() > expire_date:
            return False, "A licença expirou."
            
        return True, "Licença válida!"
        
    except Exception as e:
        return False, f"Erro ao ler a licença: {str(e)}"

def get_license_features():
    """Retorna as funcionalidades ativas na licença atual de forma segura. Retorna dict."""
    is_valid, _ = is_license_valid()
    features = {"ai_active": False}
    
    if is_valid:
        try:
            with open(LICENSE_FILE, "r") as f:
                license_key = f.read().strip()
            payload_b64 = license_key.split(".")[0]
            payload_str = base64.b64decode(payload_b64).decode()
            license_data = json.loads(payload_str)
            features["ai_active"] = bool(license_data.get("ai_active", False))
        except:
            pass
            
    return features
