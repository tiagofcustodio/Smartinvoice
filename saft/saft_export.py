import xml.etree.ElementTree as ET
from xml.dom import minidom
from core.database import get_session
from core.models import Lancamento, Fatura, Fornecedor
import os

def export_saft_mvp(filepath):
    """Gera um XML estruturado parecido com o SAFT-PT, mas versão MVP simplificada."""
    db = get_session()
    try:
        # Root SAFT
        root = ET.Element("AuditFile", xmlns="urn:OECD:StandardAuditFile-Tax:PT_1.04_01")
        
        # Header
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "AuditFileVersion").text = "1.04_01"
        ET.SubElement(header, "CompanyID").text = "500000000"
        ET.SubElement(header, "TaxRegistrationNumber").text = "500000000"
        ET.SubElement(header, "CompanyName").text = "Empresa Cliente SmartInvoice"
        ET.SubElement(header, "CurrencyCode").text = "EUR"
        
        # MasterFiles (Fornecedores e Plano de contas omitido no MVP simplificado por brevidade)
        master = ET.SubElement(root, "MasterFiles")
        
        fornecedores = db.query(Fornecedor).all()
        for f in fornecedores:
            supp = ET.SubElement(master, "Supplier")
            ET.SubElement(supp, "SupplierID").text = str(f.id)
            ET.SubElement(supp, "CompanyName").text = f.nome
            ET.SubElement(supp, "TaxRegistrationNumber").text = f.nif if f.nif else "999999990"
            
        # GeneralLedgerEntries (Lançamentos)
        ledgers = ET.SubElement(root, "GeneralLedgerEntries")
        lancamentos = db.query(Lancamento).all()
        
        ET.SubElement(ledgers, "NumberOfEntries").text = str(len(lancamentos))
        
        for idx, l in enumerate(lancamentos, 1):
            journal = ET.SubElement(ledgers, "Journal")
            trans = ET.SubElement(journal, "Transaction")
            ET.SubElement(trans, "TransactionID").text = f"MANUAL {idx}"
            ET.SubElement(trans, "Period").text = "01"
            ET.SubElement(trans, "TransactionDate").text = l.data_lancamento.strftime("%Y-%m-%d")
            
            lines = ET.SubElement(trans, "Lines")
            
            # Débito
            dline = ET.SubElement(lines, "DebitLine")
            ET.SubElement(dline, "AccountID").text = l.conta_debito
            ET.SubElement(dline, "DebitAmount").text = f"{l.valor:.2f}"
            
            # Crédito
            cline = ET.SubElement(lines, "CreditLine")
            ET.SubElement(cline, "AccountID").text = l.conta_credito
            ET.SubElement(cline, "CreditAmount").text = f"{l.valor:.2f}"
            
        # Formatar XML
        xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(xmlstr)
            
        return True, f"Ficheiro SAFT (MVP) gerado em: {filepath}"
    except Exception as e:
        return False, f"Erro ao gerar SAFT: {str(e)}"
    finally:
        db.close()
