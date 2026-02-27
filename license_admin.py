import tkinter as tk
from tkinter import ttk, messagebox
import json
import base64
import hmac
import hashlib
import datetime
from license.license_generator import SECRET_KEY, generate_license

class LicenseAdminTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Licenças - SmartInvoice (Admin)")
        self.root.geometry("600x500")
        
        # Center in screen
        self.root.eval('tk::PlaceWindow . center')
        
        self.setup_ui()
        
    def setup_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Gerar
        tab_gerar = ttk.Frame(notebook, padding=15)
        notebook.add(tab_gerar, text="Gerar Licença")
        self.setup_tab_gerar(tab_gerar)
        
        # Tab 2: Descodificar
        tab_dec = ttk.Frame(notebook, padding=15)
        notebook.add(tab_dec, text="Descodificar Licença")
        self.setup_tab_decoder(tab_dec)
        
    def setup_tab_gerar(self, frame):
        lbl_info = ttk.Label(frame, text="Gerar nova licença para um cliente:", font=("Helvetica", 12, "bold"))
        lbl_info.pack(anchor=tk.W, pady=(0, 15))
        
        ttk.Label(frame, text="Machine ID do Cliente:").pack(anchor=tk.W)
        self.entry_mid_gen = ttk.Entry(frame, width=50, font=("Courier", 11))
        self.entry_mid_gen.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame, text="Plano (Dias):").pack(anchor=tk.W, pady=(10, 0))
        self.val_dias = tk.StringVar(value="365")
        combo_dias = ttk.Combobox(frame, textvariable=self.val_dias, values=["30", "90", "180", "365", "730"], state="readonly")
        combo_dias.pack(fill=tk.X, pady=5)
        
        self.val_ai = tk.BooleanVar(value=False)
        chk_ai = ttk.Checkbutton(frame, text="Incluir módulo de Inteligência Artificial para OCR?", variable=self.val_ai)
        chk_ai.pack(anchor=tk.W, pady=(10, 5))
        
        btn_gen = ttk.Button(frame, text="Gerar Chave de Ativação", command=self.action_generate)
        btn_gen.pack(pady=15, ipady=5)
        
        ttk.Label(frame, text="Chave Gerada:").pack(anchor=tk.W)
        self.txt_key_gen = tk.Text(frame, height=5, font=("Courier", 9))
        self.txt_key_gen.pack(fill=tk.X, pady=5)
        
        btn_copy = ttk.Button(frame, text="Copiar Chave", command=lambda: self.copy_to_clipboard(self.txt_key_gen.get("1.0", tk.END).strip()))
        btn_copy.pack(anchor=tk.E)
        
    def setup_tab_decoder(self, frame):
        lbl_info = ttk.Label(frame, text="Inspecionar e Descodificar uma Chave:", font=("Helvetica", 12, "bold"))
        lbl_info.pack(anchor=tk.W, pady=(0, 15))
        
        ttk.Label(frame, text="Coloque a Chave de Ativação abaixo:").pack(anchor=tk.W)
        self.txt_key_dec = tk.Text(frame, height=5, font=("Courier", 9))
        self.txt_key_dec.pack(fill=tk.X, pady=5)
        
        btn_dec = ttk.Button(frame, text="Descodificar", command=self.action_decode)
        btn_dec.pack(pady=10, ipady=5)
        
        # Area de Resultados
        self.lbl_dec_result = ttk.Label(frame, text="Resultado:\n...", justify=tk.LEFT, background="#f0f0f0", padding=10, relief=tk.SUNKEN)
        self.lbl_dec_result.pack(fill=tk.BOTH, expand=True, pady=10)

    def action_generate(self):
        mid = self.entry_mid_gen.get().strip()
        if not mid:
            messagebox.showerror("Erro", "O Machine ID é obrigatório.")
            return
            
        try:
            dias = int(self.val_dias.get())
            ai_active = self.val_ai.get()
            key = generate_license(mid, dias, ai_active)
            
            self.txt_key_gen.delete("1.0", tk.END)
            self.txt_key_gen.insert(tk.END, key)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro a gerar chave: {str(e)}")

    def action_decode(self):
        key = self.txt_key_dec.get("1.0", tk.END).strip()
        if not key or "." not in key:
            self.lbl_dec_result.config(text="Erro: Formato de chave inválido. Certifique-se que copiou a chave completa.", foreground="red")
            return
            
        try:
            payload_b64, signature = key.split(".", 1)
            
            # Verificar integridade da Assinatura
            expected_signature = hmac.new(SECRET_KEY, payload_b64.encode(), hashlib.sha256).hexdigest()
            is_valid_sig = hmac.compare_digest(signature, expected_signature)
            
            # Descodificar JSON
            payload_str = base64.b64decode(payload_b64).decode()
            data = json.loads(payload_str)
            
            mid = data.get("machine_id", "Desconhecido")
            expires = data.get("expires", "Desconhecido")
            plan = data.get("plan_days", "N/A")
            ai_active = data.get("ai_active", False)
            
            hoje = datetime.datetime.utcnow()
            try:
                exp_date = datetime.datetime.strptime(expires, "%Y-%m-%d")
                is_expired = hoje > exp_date
                status_tempo = "EXPIRADA" if is_expired else "DENTRO DA VALIDADE"
            except:
                status_tempo = "ERRO A LER DATA"

            sig_status = "VÁLIDA (Não foi adulterada)" if is_valid_sig else "INVÁLIDA (A chave foi adulterada)"
            
            resultado = (
                f"--- DETALHES DA CHAVE ---\n\n"
                f"Machine ID Alvo : {mid}\n"
                f"Plano Original  : {plan} dias\n"
                f"Data Expiração  : {expires}\n"
                f"IA Gemini Ativo?: {'SIM' if ai_active else 'NÃO'}\n\n"
                f"Estado do Tempo : {status_tempo}\n"
                f"Assinatura HMAC : {sig_status}"
            )
            
            cor = "black" if is_valid_sig else "red"
            self.lbl_dec_result.config(text=resultado, foreground=cor)
            
        except Exception as e:
            self.lbl_dec_result.config(text=f"Erro crítico a ler chave:\n{str(e)}", foreground="red")

    def copy_to_clipboard(self, text):
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("Copiado", "Chave copiada com sucesso!")

def main():
    root = tk.Tk()
    app = LicenseAdminTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()
