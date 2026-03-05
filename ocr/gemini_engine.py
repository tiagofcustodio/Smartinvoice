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
        is_pdf = file_path.lower().endswith(".pdf")
        
        if is_pdf:
            uploaded_file = client.files.upload(file=file_path)
            # Para PDFs vamos passar o ficheiro carregado para a API
        else:
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
        Retorna APENAS E EXCLUSIVAMENTE um objeto JSON válido, sem mais nenhum texto, com a seguinte estrutura. Se algum campo não for encontrado, o valor deve ser `null`.
{{
  "nif": "número de identificação fiscal do fornecedor (9 dígitos, sem espaços)",
  "fornecedor_nome": "nome da entidade que emitiu a fatura",
  "data": "data da fatura no formato YYYY-MM-DD",
  "total": "valor total a pagar (FLOAT), usando PONTO como separador decimal. Exemplo: 12.50",
  "categoria": "Analisando os produtos e o fornecedor, tenta categorizar numa destas opções: 'Supermercado', 'Combustível', 'Material Elétrico', 'Materiais Construção', 'Restaurante', 'Telecomunicações', 'Equipamento', 'Saúde', 'Despesas Gerais Familiares' ou 'Outros'.",
  "categoria_irs": "Deduz a que categoria de IRS deduzível esta fatura pertence baseado no Fornecedor/Artigos. Opções válidas: 'Saúde', 'Educação', 'Habitação', 'Lares', 'Oficinas', 'Restauração e Alojamento', 'Atividades Veterinárias', 'Passes Mensais', 'Cabeleireiros', 'Ginásios', ou se nenhuma encaixar 'Despesas Gerais Familiares'.",
  "artigos": [
    {{
      "descricao": "nome ou descrição do produto/serviço",
      "taxa_iva": "taxa de IVA aplicável em percentagem ex: 0, 6, 13 ou 23 (FLOAT). Não inclua o símbolo %",
      "valor": "valor total da linha/artigo a que diz respeito (FLOAT)"
    }}
  ]
}}
        Não incluas Markdown como ```json nas extremidades.
        """
        
        if is_pdf:
            contents = [uploaded_file, prompt]
        else:
            contents = [img, prompt]
            
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )
        
        # Limpar o ficheiro PDF do storage do Gemini para não ocupar espaço
        if is_pdf:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass
        
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
