import hmac
import hashlib
import json
import base64
import os
import datetime

# Chave secreta que SÓ TU conheces (o cliente não tem acesso ao generator)
SECRET_KEY = b"SMARTINVOICE_SUPER_SECRET_KEY_2026_CHANGE_ME"

def generate_license(machine_id, plan_days, ai_active=False):
    """Gera uma licença baseada no Machine ID inserido no formato HMAC assinado."""
    expiration_date = datetime.datetime.utcnow() + datetime.timedelta(days=plan_days)
    
    license_data = {
        "machine_id": machine_id,
        "expires": expiration_date.strftime("%Y-%m-%d"),
        "plan_days": plan_days,
        "ai_active": ai_active
    }
    
    payload_str = json.dumps(license_data, separators=(',', ':'))
    payload_b64 = base64.b64encode(payload_str.encode()).decode()
    
    # Assinatura
    signature = hmac.new(SECRET_KEY, payload_b64.encode(), hashlib.sha256).hexdigest()
    
    license_key = f"{payload_b64}.{signature}"
    return license_key

if __name__ == "__main__":
    print("--- Gerador de Licenças ---")
    mid = input("Insira o Machine ID do cliente: ").strip()
    plan = int(input("Dias do plano (ex: 90, 180, 365): ").strip())
    ai_choice = input("Incluir suporte a Inteligência Artificial / Gemini? (S/N): ").strip().lower()
    ai_active = ai_choice == 's'
    
    key = generate_license(mid, plan, ai_active)
    print("\n[SUCESSO] Chave gerada:")
    print(key)
    print("\nEnvie esta chave para o cliente.")
