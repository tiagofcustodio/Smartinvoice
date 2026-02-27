import re

text = """
Farmácia LUZ
F Luz Sociedade Unipessoal Lda
Dir. Téc. Dra. Angela M.C.de Cezar Pint
Tel. 214870635
Rua de Cascais, 957 - Malveira da Serra
Contr. N 517278499

2026-02-25 18:44   (9)

Factura / Recibo Nº FR 8/82087
N. Cliente: 2873
ANDREIA ALEXANDRA RODRIGUES CASCAREJO

Contribuinte n.239976294

Designação
   PVP     P.Ref.  %SNS   SNS   Preço
     Código   IVA     Qtd       Total
Baycuten, 10/0,4 mg/g x 30 creme bisn
  8,94        0      0       8,94
   9524033   6      1       8,94
Gyno-Pevaryl, 150 mg x 3 óvulo
  9,40        0      0       9,40
   8439711   6      1       9,40

Total EUR ................ : 18,34

Taxa Base      IVA     Total
  6% € 17,30   € 1,04  € 18,34
"""

def test_parse(text):
    data = {"nif": None, "data": None, "total": None, "artigos": []}
    
    # 1. NIF with context
    nif_pattern = r'\b[1235689]\d{8}\b'
    # Try to find NIF with keyword prefix first
    context_nifs = re.findall(r'(?i)(?:nif|contribuinte|contr\.?)[^\d]*([1235689]\d{8})\b', text)
    if context_nifs:
        data["nif"] = context_nifs[0]
    else:
        nifs = re.findall(nif_pattern, text)
        if nifs: data["nif"] = nifs[0]
        
    # 2. Add YYYY-MM-DD support to Date
    date_matches = re.findall(r'\b(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})\b', text)
    if date_matches:
        data["data"] = date_matches[0].replace('/', '-')
        
    # 3. Items Multi-line fallback
    lines = text.split('\n')
    
    # Basic list of stop words
    stop_words = ['total', 'sum', 'pagar', 'iva', 'base inc', 'troco', 'designação', 'código', 'pvp']
    
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if len(line_clean) < 5: continue
        lower_line = line_clean.lower()
        if any(skip in lower_line for skip in stop_words): continue
        
        # Original UN heuristic here...
        
        # New multi-line heuristic:
        # If line has no strict price, check if next line HAS a price and is mostly numbers
        price_pattern = r'\b\d+[,.]\d{2}\b'
        price_match = re.search(price_pattern, line_clean)
        
        if not price_match and i < len(lines) - 1:
            next_line = lines[i+1].strip()
            next_prices = re.findall(price_pattern, next_line)
            if next_prices:
                # Looks like a description followed by a price line
                # Make sure the description line has some text (not just numbers)
                letters = sum(c.isalpha() for c in line_clean)
                if letters > 5:
                    # It's an item!
                    # Price is usually the last match in the line (e.g. Total of the item)
                    val_str = next_prices[-1].replace(',', '.')
                    data["artigos"].append({
                        "descricao": line_clean[:200],
                        "valor": float(val_str)
                    })

    return data

result = test_parse(text)
import json
print(json.dumps(result, indent=2, ensure_ascii=False))
