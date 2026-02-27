from core.models import Fornecedor, Categoria
from core.database import get_session

def guess_supplier_and_category(text):
    """
    Tenta adivinhar o fornecedor e a categoria com base no texto extraído.
    Se encontrar o NIF no texto, cruza com a BD.
    Se não, procura por palavras-chave (Ex: GALP, BP, CONTINENTE).
    """
    db = get_session()
    
    # 1. Procurar por palavras-chave comuns fixas (fallback)
    regras_basicas = {
        "galp": "Combustível",
        "bp": "Combustível",
        "repsol": "Combustível",
        "prio": "Combustível",
        "continente": "Supermercado",
        "pingo doce": "Supermercado",
        "lidl": "Supermercado",
        "auchan": "Supermercado",
        "nos": "Telecomunicações",
        "meo": "Telecomunicações",
        "vodafone": "Telecomunicações",
        "worten": "Equipamento",
        "fnac": "Equipamento",
        "staples": "Material escritório",
        "globlec": "Material Elétrico",
        "leroy merlin": "Materiais Construção",
        "maxmat": "Materiais Construção",
        "ikea": "Mobiliário"
    }
    
    texto_lower = text.lower()
    
    sugerido_nome = "Desconhecido"
    sugerido_categoria_nome = "Outros"
    
    # Verifica regras hardcoded básicas
    for chave, cat_nome in regras_basicas.items():
        if chave in texto_lower:
            sugerido_nome = chave.capitalize()
            sugerido_categoria_nome = cat_nome
            break
            
    # TODO: Podia-se pesquisar na base de dados se existe nomes semelhantes (LIKE) 
    # ou correspondência pelo NIF (Extraído pelo parser)
    
    db.close()
    return sugerido_nome, sugerido_categoria_nome
