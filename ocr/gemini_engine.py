import os
import json
from google import genai
from PIL import Image, ImageOps

# O administrador terá a sua API Key definida numa variável de ambiente do sistema 
# na máquina do utilizador ou, para testes locais, via config.py
# (Recomendação: O dono do software configura o SO do cliente com o GOOGLE_API_KEY)
def get_gemini_client():
    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            # Fallback seguro para procurar num ficheiro se aplicável
            key_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gemini_api_key.txt")
            if not os.path.exists(key_file):
                key_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gemini.key")
            if os.path.exists(key_file):
                with open(key_file, "r") as f:
                    api_key = f.read().strip()
        
        if not api_key:
            return None
            
        return genai.Client(api_key=api_key)
    except Exception:
        return None

def extract_structured_data_with_gemini(file_path):
    """
    Submete a imagem do recibo ao Gemini 2.5 Flash juntamente 
    com instruções estritas para retornar apenas o JSON com os dados cruciais.
    Substitui a necessidade do parser.py heurístico!
    """
    client = get_gemini_client()
    if not client:
        raise Exception("API Key do Gemini em falta ou mal configurada.")
        
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Ficheiro não encontrado: {file_path}")
        
    try:
        # Carrega imagem e corrige rotação se via telemóvel
        img = Image.open(file_path)
        img = ImageOps.exif_transpose(img)
        
        # Obter contexto do perfil atual
        from core.database import get_session
        from core.models import DefinicoesPerfil
        db = get_session()
        nifs_permitidos_texto = ""
        try:
            definicao = db.query(DefinicoesPerfil).first()
            if definicao and definicao.nifs_associados:
                lista_nifs = json.loads(definicao.nifs_associados)
                if lista_nifs:
                    nifs = [item.get("nif") for item in lista_nifs if item.get("nif")]
                    nomes = [item.get("nome") for item in lista_nifs if item.get("nome")]
                    nifs_permitidos_texto = f'Atenção! Esta conta pertence a {", ".join(nomes)}. O NIF de adquirente a procurar nesta fatura SÓ pode ser considerado se pertencer à seguinte lista: {", ".join(nifs)}.'
        except Exception:
            pass
        finally:
            db.close()
        
        prompt = f"""
        És um sistema de extração de faturas, talões e recibos portugueses altamente rigoroso.
        Dado o documento anexo (que pode ter ruído ou texto irrelevante), extrai os dados seguintes rigidamente em formato JSON:
        
        {nifs_permitidos_texto}
        1. "nif": O Número de Identificação Fiscal do utilizador que pagou a fatura. Ignora qualquer NIF que pertença nitidamente à loja/empresa emissora. Geralmente tem 9 dígitos. Se Não encontrares, devolve null.
        2. "data": A data de emissão formatada EXATAMENTE em "YYYY-MM-DD".
        3. "fornecedor_nome": O Nome Comercial da entidade emissora (quem vendeu/prestou o serviço). REGRA DE OURO: O fornecedor NUNCA pode ser a própria empresa cliente (neste caso, a conta pertence a: {", ".join(nomes) if 'nomes' in locals() and nomes else 'si'}). Numa fatura existe SEMPRE o nome de um fornecedor fornecedor. Se o nome/entidade principal que encontrares for o da própria empresa cliente, então OBRIGATORIAMENTE tens de procurar o OUTRO nome de empresa que aparece no documento e usá-lo como fornecedor! Não incluas a forma jurídica completa, apenas o nome curto (ex: "Globlec" em vez de "GLOBLEC - LDA").
        4. "categoria": Analisando os produtos e o fornecedor, tenta categorizar obrigatoriamente numa destas opções: 
           "Supermercado", "Combustível", "Material Elétrico", "Materiais Construção", "Restaurante", "Telecomunicações", "Equipamento", "Saúde" ou "Outros".
        5. "total": O "Total a Pagar" ou valor líquido final na fatura. Tem de ser um float (ex: 59.26). Ignora subtotais ou valores de incidência/IVA.
        6. "artigos": Uma lista APENAS com os produtos reais comprados. REGRA DE OURO: Para não obteres falso-positivos, SÓ deves processar uma linha como "artigo" se esta possuir um respetivo Código de Artigo / Referência / SKU na fatura (ex: códigos alfanuméricos como "17EE805A", "2190601TBR" ou EANs de código de barras). Linhas sem referência (como portes, observações, adiantamentos, texto livre) DEVEM ser completamente ignoradas.
           O formato deve ser rigorosamente: [{{"descricao": "Nome do Artigo Real", "valor": PreçoFinalDaLinhaComoFloat}}]
        
        Retorna MERA E EXCLUSIVAMENTE o bloco de código JSON final, nada mais. Começa logo com {{ e acaba em }}.
        Não incluas Markdown como ```json nas extremidades.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[img, prompt]
        )
        
        # O modelo pode ocasionalmente meter dentro de um bloco ```json ... ```
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "", 1)
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
        
        raw_text = raw_text.strip()
        data = json.loads(raw_text)
        
        return data

    except Exception as e:
        raise Exception(f"Falha na inferência do Gemini: {str(e)}")
