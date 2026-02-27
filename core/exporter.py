import os
import pandas as pd
from core.database import get_session
from core.models import Fatura, Fornecedor, Categoria, ArtigoFatura
from config import BASE_DIR
import datetime

# Pasta onde os relatórios serão guardados
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")

def ensure_exports_dir():
    if not os.path.exists(EXPORTS_DIR):
        os.makedirs(EXPORTS_DIR, exist_ok=True)

def export_monthly_reports(mes_selecionado):
    """
    Gera um ficheiro Excel (.xlsx) contendo duas folhas visuais:
    1. Lista Faturas (Resumo do mês)
    2. Lista Artigos (Detalhe grão a grão de cada produto comprado)
    """
    ensure_exports_dir()
    db = get_session()
    
    try:
        # 1. Obter todas as faturas do mês selecionado
        faturas = db.query(Fatura, Fornecedor, Categoria).\
            outerjoin(Fornecedor, Fatura.fornecedor_id == Fornecedor.id).\
            outerjoin(Categoria, Fatura.categoria_id == Categoria.id).\
            filter(Fatura.data.like(f"{mes_selecionado}%")).all()
            
        if not faturas:
            return False, "Sem dados para exportar neste mês."
            
        # Preparar dados para o separador Faturas
        faturas_data = []
        faturas_ids = []
        for ft, fn, cat in faturas:
            faturas_ids.append(ft.id)
            faturas_data.append({
                "ID Fatura": ft.id,
                "Data": ft.data,
                "Fornecedor": fn.nome if fn else "Desconhecido",
                "NIF Fornecedor": fn.nif if fn and fn.nif else "",
                "Categoria": cat.nome if cat else "Não Classificado",
                "Total (€)": round(ft.total, 2) if ft.total else 0.0,
                "Estado": ft.estado
            })
            
        df_faturas = pd.DataFrame(faturas_data)
        
        # 2. Obter todos os artigos que pertencem a estas faturas
        artigos = db.query(ArtigoFatura, Fatura, Fornecedor).\
            join(Fatura, ArtigoFatura.fatura_id == Fatura.id).\
            outerjoin(Fornecedor, Fatura.fornecedor_id == Fornecedor.id).\
            filter(ArtigoFatura.fatura_id.in_(faturas_ids)).all()
            
        artigos_data = []
        for art, ft, fn in artigos:
            artigos_data.append({
                "Data Fatura": ft.data,
                "Fornecedor": fn.nome if fn else "Desconhecido",
                "Artigo / Descrição": art.descricao,
                "Valor (€)": round(art.valor, 2) if art.valor else 0.0
            })
            
        df_artigos = pd.DataFrame(artigos_data)
        
        # 3. Gerar o ficheiro Excel
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Relatorio_Despesas_{mes_selecionado.replace('-', '_')}_{timestamp}.xlsx"
        filepath = os.path.join(EXPORTS_DIR, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df_faturas.to_excel(writer, sheet_name='Resumo Faturas', index=False)
            if not df_artigos.empty:
                df_artigos.to_excel(writer, sheet_name='Detalhe Artigos', index=False)
                
        return True, filepath
        
    except Exception as e:
        return False, str(e)
    finally:
        db.close()
