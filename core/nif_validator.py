import requests

def validate_nif_vies(nif):
    """
    Verifica a validade de um NIF no portal europeu VIES (Vat Information Exchange System).
    Retorna o Nome da Empresa (Razão Social) e a Morada se o NIF for válido.
    Assume 'PT' como prefixo se o NIF só tiver 9 dígitos.
    """
    if not nif:
        return False, "Desconhecido", "Morada Desconhecida"
        
    nif_str = str(nif).replace(" ", "").upper()
    
    # Se o utilizador apenas leu 9 algarismos, assumimos PT
    if len(nif_str) == 9 and nif_str.isdigit():
        country_code = "PT"
        vat_number = nif_str
    elif len(nif_str) > 2:
        country_code = nif_str[:2]
        vat_number = nif_str[2:]
    else:
        return False, "Desconhecido", "Morada Desconhecida"

    # API Pública VIES (REST via VIES API)
    url = f"https://ec.europa.eu/taxation_customs/vies/rest-api/ms/{country_code}/vat/{vat_number}"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            is_valid = data.get("isValid", False)
            if is_valid:
                nome = data.get("name", "").strip().title() or "Desconhecido"
                morada = data.get("address", "").strip() or "Morada Desconhecida"
                # Limpa a string da morada que muitas vezes vem com \n de formatação europeia
                morada = " - ".join([part.strip() for part in morada.split("\n") if part.strip()])
                return True, nome, morada
                
        return False, "Desconhecido", "Morada Desconhecida"
    except Exception as e:
        print(f"Erro ao validar NIF {nif} no VIES: {e}")
        return False, "Desconhecido", "Morada Desconhecida"
