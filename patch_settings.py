import sys
import codecs

with codecs.open('ui/settings_view.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Imports
orig_imports = "import datetime\nfrom license.license_manager import get_machine_id\nfrom license.validator import LICENSE_FILE, is_license_valid, get_license_features\n\nclass SettingsView(ttk.Frame):"
new_imports = "import datetime\nfrom license.license_manager import get_machine_id\nfrom license.validator import LICENSE_FILE, is_license_valid, get_license_features\nimport os\n\nGEMINI_KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gemini.key')\n\nclass SettingsView(ttk.Frame):"
content = content.replace(orig_imports, new_imports)

# 2. UI Entry
orig_ui = '        btn_update_license = ttk.Button(self.frame_license, text="Atualizar Licença", command=self.update_license, style="Accent.TButton")\n        btn_update_license.grid(row=3, column=2, sticky=tk.W, pady=(15, 2), padx=10)\n\n        # Tipo de Perfil'
new_ui = '''        btn_update_license = ttk.Button(self.frame_license, text="Atualizar Licença", command=self.update_license, style="Accent.TButton")
        btn_update_license.grid(row=3, column=2, sticky=tk.W, pady=(15, 2), padx=10)

        ttk.Label(self.frame_license, text="Chave API Google Gemini:").grid(row=4, column=0, sticky=tk.W, pady=(5, 2), padx=5)
        self.entry_gemini_key = ttk.Entry(self.frame_license, width=50, show="*")
        self.entry_gemini_key.grid(row=4, column=1, sticky=tk.W, pady=(5, 2), padx=5)
        
        btn_update_gemini = ttk.Button(self.frame_license, text="Guardar API GenAI", command=self.update_gemini_key)
        btn_update_gemini.grid(row=4, column=2, sticky=tk.W, pady=(5, 2), padx=10)

        # Tipo de Perfil'''
content = content.replace(orig_ui, new_ui)

# 3. Logic
orig_logic = '''        else:
            self.lbl_days.config(text=f"Inválida ou Expirada: {msg}", foreground="red")
            self.lbl_ai.config(text="--")
            
    def update_license(self):'''
new_logic = '''        else:
            self.lbl_days.config(text=f"Inválida ou Expirada: {msg}", foreground="red")
            self.lbl_ai.config(text="--")
            
        if os.path.exists(GEMINI_KEY_FILE):
            try:
                with open(GEMINI_KEY_FILE, "r") as f:
                    self.entry_gemini_key.delete(0, tk.END)
                    self.entry_gemini_key.insert(0, f.read().strip())
            except Exception:
                pass
                
    def update_gemini_key(self):
        new_gemini = self.entry_gemini_key.get().strip()
        try:
            with open(GEMINI_KEY_FILE, "w") as f:
                f.write(new_gemini)
            messagebox.showinfo("Sucesso", "Chave API do Google Gemini guardada com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível guardar a API Key: {e}")

    def update_license(self):'''
content = content.replace(orig_logic, new_logic)

with codecs.open('ui/settings_view.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"File updated. orig_imports found: {orig_imports in content}, orig_ui found: {orig_ui in content}, orig_logic found: {orig_logic in content}")
