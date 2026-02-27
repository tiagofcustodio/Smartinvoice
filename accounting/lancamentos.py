from core.database import get_session
from core.models import Fatura, Lancamento, Categoria
import datetime

def gerar_lancamento_automatico(fatura_id):
    """
    Gera as entradas de débito e crédito para uma conta baseada na fatura.
    No MVP:
    Débito -> Conta de Gastos (Ex: 624 - Combustíveis)
    Crédito -> Conta de Caixa (Ex: 11 - Caixa) ou Bancos (Ex: 12 - Bancos)
    """
    db = get_session()
    try:
        fatura = db.query(Fatura).filter(Fatura.id == fatura_id).first()
        if not fatura or fatura.estado == "Contabilizada":
            return False, "Fatura não encontrada ou já contabilizada."
            
        categoria = db.query(Categoria).filter(Categoria.id == fatura.categoria_id).first()
        conta_deb = categoria.conta_debito_codigo if categoria and categoria.conta_debito_codigo else "62"
        
        # Criação do Lançamento
        lancamento = Lancamento(
            fatura_id=fatura.id,
            conta_debito=conta_deb,
            conta_credito="11", # Assume pagamento direto por Caixa para o MVP
            valor=fatura.total,
            data_lancamento=datetime.datetime.utcnow()
        )
        
        # Atualiza Fatura
        fatura.estado = "Contabilizada"
        
        db.add(lancamento)
        db.commit()
        return True, "Lançamento gerado com sucesso."
        
    except Exception as e:
        db.rollback()
        return False, f"Erro ao gerar lançamento: {str(e)}"
    finally:
        db.close()
