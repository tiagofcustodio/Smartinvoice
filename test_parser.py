import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from ocr.parser import parse_invoice_text

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

result = parse_invoice_text(text)
import json
print(json.dumps(result, indent=2, ensure_ascii=False))
