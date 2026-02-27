import requests
from config import APP_VERSION

# Nota: Em produção, este link devia ser um servidor remoto. 
# Como nos pediram uma porta paralela com este mini servidor incluído, usamos localhost.
UPDATE_SERVER_URL = "http://localhost:5000/api/update"

def check_for_updates():
    """
    Verifica se a versão da internet é superior à versão atual.
    Retorna uma tuple: (tem_update: bool, latest_version: str, download_url: str, release_notes: str)
    """
    try:
        response = requests.get(UPDATE_SERVER_URL, timeout=3)
        if response.status_code == 200:
            data = response.json()
            latest = data.get("latest_version", APP_VERSION)
            
            # Uma comparação de strings simples funciona para "1.0.0" vs "1.1.0"
            # Num cenário mais complexo deveríamos usar 'packaging.version.parse'
            has_update = latest > APP_VERSION
            
            return (
                has_update, 
                latest, 
                data.get("download_url", ""), 
                data.get("release_notes", "")
            )
            
    except requests.exceptions.RequestException as e:
        print(f"Erro ao verificar atualização no servidor de Update: {e}")
        
    return False, APP_VERSION, "", "A verificar..."
