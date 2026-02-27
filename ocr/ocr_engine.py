import pytesseract
import os
from PIL import Image, ImageOps
from pdf2image import convert_from_path

# Apontar explicitamente para o instalável comum de Windows que o utilizador instalou
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Diretório local para os dicionários de linguagem
TESSDATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tessdata")
CUSTOM_CONFIG = f'--tessdata-dir "{TESSDATA_DIR}"'

def extract_text(file_path):
    """Extrai texto de um ficheiro de imagem ou PDF usando Tesseract OCR"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Ficheiro não encontrado: {file_path}")
        
    try:
        # Check if PDF
        if file_path.lower().endswith('.pdf'):
            images = convert_from_path(file_path)
            text = ""
            for img in images:
                text += pytesseract.image_to_string(img, lang="por", config=CUSTOM_CONFIG)
            return text
        else:
            # Assume Image (JPG, PNG)
            img = Image.open(file_path)
            # Corrigir rotação baseada no EXIF (telemóveis)
            img = ImageOps.exif_transpose(img)
            return pytesseract.image_to_string(img, lang="por", config=CUSTOM_CONFIG)
    except Exception as e:
        return f"ERRO ao processar imagem: {str(e)}"
    else:
        text = "Formato não suportado."
        
    return text
