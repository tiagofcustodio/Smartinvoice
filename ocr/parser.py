import re

def parse_invoice_text(text):
    """Analisa o texto extraído da fatura e encontra NIF, Data e Total"""
    
    artigos_list = []
    data = {
        "nif": None,
        "data": None,
        "total": None,
        "fornecedor_nome": "Desconhecido", # ML simplificado preenche isto depois
        "artigos": artigos_list
    }
    
    # 1. Encontrar NIF Português (9 dígitos, muitas vezes começa com 5 ou 2)
    # Procuramos o primeiro bloco de 9 números que venha a seguir a um contexto válido
    context_nifs = re.findall(r'(?i)(?:nif|contribuinte|contr\.?)[^\d]*([1235689]\d{8})\b', text)
    if context_nifs:
        data["nif"] = context_nifs[0]
    else:
        nif_matches = re.findall(r'\b[1235689]\d{8}\b', text)
        if nif_matches:
            data["nif"] = nif_matches[0]
        
    # 2. Encontrar Data (Formatos comuns DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, YYYY/MM/DD)
    date_matches = re.findall(r'\b(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})\b', text)
    if date_matches:
        # Pega a primeira data que pareça válida
        data["data"] = date_matches[0].replace('/', '-')
        
    # 3. Encontrar Total / Valor a Pagar
    # Ex: Total: 100,50 | EUR 100.50 | 1.000,50
    # Procuramos os maiores números preenchidos como moeda
    # (heurística básica, o ideal seria procurar por "Total", "TOTAL A PAGAR", etc.)
    lines = text.split('\n')
    possible_totals = []
    
    for line in lines:
        if 'total' in line.lower() or 'pagar' in line.lower() or 'sum' in line.lower():
            # Tentar encontrar valor nessa linha
            # Aceita 100,00 ou 100.00 ou 1.000,00
            money_match = re.search(r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})', line)
            if money_match:
                possible_totals.append(money_match.group(1))
                
    if possible_totals:
        # Pega a última correspondência na linha que disse 'total' (costuma ser o valor final)
        val_str = possible_totals[-1].replace('.', '').replace(',', '.')
        try:
            data["total"] = float(val_str)
        except ValueError:
            pass
            
    # Fallback se a heurística de "Total" falhar, pegar o número mais alto no texto (arriscado, mas serve para MVP)
    if not data["total"]:
        all_money = re.findall(r'\b(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})\b', text)
        if all_money:
            try:
                # Converte todos para float
                floats = [float(x.replace('.', '').replace(',', '.')) for x in all_money]
                data["total"] = max(floats)
            except ValueError:
                pass
                
    # 4. Encontrar Artigos Individuais
    # Como as faturas em papel têm colunas largas, o Tesseract muitas vezes parte a linha ao meio
    # Vamos usar uma heurística baseada na unidade de medida (ex: UN, KG, Mts) e de múltiplas linhas.
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if len(line_clean) < 5: continue
        
        # Ignora linhas que são só totais
        lower_line = line_clean.lower()
        stop_words = ['total', 'sum', 'pagar', 'iva', 'base inc', 'troco', 'designação', 'código', 'pvp']
        if any(skip in lower_line for skip in stop_words):
            continue
            
        # Procurar o padrão " UN " (Unidade) muito comum nas faturas
        if " UN " in line_clean or " un " in line_clean:
            # Divide a linha a meio exatamente na palavra UN
            parts = re.split(r'\bUN\b|\bun\b', line_clean, maxsplit=1)
            desc = parts[0].strip()
            
            # Remover os códigos do artigo que costumam vir antes do nome descritivo (opcional mas limpa ficheiro)
            desc = re.sub(r'^[\w\d-]+\s+', '', desc)
            
            if len(desc) < 3:
                continue
                
            # Tentar encontrar preços na parte direita do "UN" (quantidade x preço = valor)
            # Retiramos espaços extra que o Tesseract põe à toa nos números ex: 29 58 -> 2958
            right_side = parts[1].replace(' ', '')
            val_str = "0.00"
            
            # Uma regex mais permissiva: \d+[,.]\d{2}
            money_match = re.search(r'(\d+)[.,](\d{2})', right_side)
            if money_match:
                val_str = f"{money_match.group(1)}.{money_match.group(2)}"
            else:
                 # Se o OCR destruiu a vírgula do preço (ex: 2956), assumir ultimos dois digitos como decimais
                 nums = re.findall(r'\d+', right_side)
                 if nums:
                     last_num = nums[-1]
                     if len(last_num) >= 3:
                         val_str = f"{last_num[:-2]}.{last_num[-2:]}"
                     else:
                         val_str = f"{last_num}.00"
                 
            try:
                artigos_list.append({
                    "descricao": desc[:200],
                    "valor": float(val_str)
                })
            except ValueError:
                pass
        else:
            # Heurística para recibos POS de múltiplas linhas onde a descrição vem numa linha 
            # e o preço unitário e quantias chegam soltos na linha de baixo (ex. Farmácia)
            price_pattern = r'\b\d+[,.]\d{2}\b'
            price_match = re.search(price_pattern, line_clean)
            
            if not price_match and i < len(lines) - 1:
                next_line = lines[i+1].strip()
                next_prices = re.findall(price_pattern, next_line)
                if next_prices:
                    # Parece a descrição de um artigo com o valor na linha seguinte
                    letters = sum(c.isalpha() for c in line_clean)
                    if letters > 5:
                        val_str = next_prices[-1].replace(',', '.')
                        try:
                            artigos_list.append({
                                "descricao": line_clean[:200],
                                "valor": float(val_str)
                            })
                        except ValueError:
                            pass

    return data
