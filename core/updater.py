import requests
from config import APP_VERSION

# URL da API do GitHub para obter a última release ("Lançamento") deste repositório
GITHUB_API_URL = "https://api.github.com/repos/tiagofcustodio/Smartinvoice/releases/latest"

def check_for_updates():
    """
    Verifica se a versão no GitHub é superior à versão atual (APP_VERSION).
    Retorna uma tuple: (tem_update: bool, latest_version: str, download_url: str, release_notes: str)
    """
    try:
        response = requests.get(GITHUB_API_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # A tag no GitHub costuma vir com ou sem "v". Ex: "v1.1.0" ou "1.1.0"
            latest_tag = data.get("tag_name", APP_VERSION)
            latest_clean = latest_tag.replace("v", "")
            current_clean = APP_VERSION.replace("v", "")
            
            # Uma comparação de strings simples funciona para "1.0.0" vs "1.1.0"
            has_update = latest_clean > current_clean
            
            # html_url leva o utilizador à página no GitHub para ler e descarregar o novo executável/código
            return (
                has_update, 
                latest_clean, 
                data.get("html_url", ""), 
                data.get("body", "Atualização de melhorias e correções de bugs.")
            )
            
    except requests.exceptions.RequestException as e:
        print(f"Erro ao verificar atualização no GitHub: {e}")
        
    return False, APP_VERSION, "", "A verificar..."
