import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from core.database import get_session
from core.models import DefinicoesPerfil
import json
import os
import base64
import datetime
from license.license_manager import get_machine_id
from license.validator import LICENSE_FILE, is_license_valid, get_license_features

class SettingsView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.nifs_list = []
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        lbl_title = ttk.Label(self, text="⚙️ Definições do Perfil", font=("Segoe UI", 16, "bold"))
        lbl_title.pack(anchor=tk.W, pady=(0, 20))
        
        # --- Licenciamento ---
        self.frame_license = ttk.LabelFrame(self, text="🔑 Licenciamento e Machine ID", padding=15)
        self.frame_license.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(self.frame_license, text="Seu Machine ID:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=2, padx=5)
        self.ent_machine_id = ttk.Entry(self.frame_license, width=30)
        self.ent_machine_id.insert(0, get_machine_id())
        self.ent_machine_id.configure(state="readonly")
        self.ent_machine_id.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(self.frame_license, text="Dias Restantes:", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=2, padx=5)
        self.lbl_days = ttk.Label(self.frame_license, text="--")
        self.lbl_days.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(self.frame_license, text="Módulo Inteligência Artificial:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=2, padx=5)
        self.lbl_ai = ttk.Label(self.frame_license, text="--")
        self.lbl_ai.grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(self.frame_license, text="Nova Chave de Licença:").grid(row=3, column=0, sticky=tk.W, pady=(15, 2), padx=5)
        self.entry_new_key = ttk.Entry(self.frame_license, width=50)
        self.entry_new_key.grid(row=3, column=1, sticky=tk.W, pady=(15, 2), padx=5)
        
        btn_update_license = ttk.Button(self.frame_license, text="Atualizar Licença", command=self.update_license, style="Accent.TButton")
        btn_update_license.grid(row=3, column=2, sticky=tk.W, pady=(15, 2), padx=10)

        # Tipo de Perfil
        frame_tipo = ttk.LabelFrame(self, text="Tipo de Perfil", padding=15)
        frame_tipo.pack(fill=tk.X, pady=(0, 20))
        
        self.var_tipo = tk.StringVar(value="Pessoal")
        
        rb_pessoal = ttk.Radiobutton(frame_tipo, text="Pessoal (Agregado Familiar)", variable=self.var_tipo, value="Pessoal", command=self.update_ui_state)
        rb_pessoal.pack(side=tk.LEFT, padx=(0, 20))
        
        rb_empresa = ttk.Radiobutton(frame_tipo, text="Empresarial", variable=self.var_tipo, value="Empresarial", command=self.update_ui_state)
        rb_empresa.pack(side=tk.LEFT)
        
        # Regime de IVA
        frame_regime = ttk.LabelFrame(self, text="Regime de IVA", padding=15)
        frame_regime.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(frame_regime, text="Escolha a forma como o IVA será apurado e declarado (para apresentar os devidos relatórios):").pack(anchor=tk.W, pady=(0, 10))
        self.var_regime = tk.StringVar(value="Isento (Art. 53º)")
        cb_regime = ttk.Combobox(frame_regime, textvariable=self.var_regime, state="readonly", values=["Isento (Art. 53º)", "Normal Trimestral", "Normal Mensal"])
        cb_regime.pack(fill=tk.X)
        
        # Detalhes
        self.frame_details = ttk.LabelFrame(self, text="NIFs Autorizados", padding=15)
        self.frame_details.pack(fill=tk.BOTH, expand=True)
        
        # Top bar of details
        top_bar = ttk.Frame(self.frame_details)
        top_bar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_bar, text="O SmartInvoice utilizará estes NIFs para confirmar se a fatura lhe pertence.").pack(side=tk.LEFT)
        btn_add = ttk.Button(top_bar, text="+ Adicionar NIF", command=self.add_nif, style="Accent.TButton")
        btn_add.pack(side=tk.RIGHT)
        btn_remove = ttk.Button(top_bar, text="- Remover NIF", command=self.remove_nif)
        btn_remove.pack(side=tk.RIGHT, padx=5)
        
        # Lista
        columns = ("username", "nif", "nome")
        self.tree = ttk.Treeview(self.frame_details, columns=columns, show="headings", height=8)
        self.tree.heading("username", text="Utilizador")
        self.tree.heading("nif", text="NIF")
        self.tree.heading("nome", text="Nome Associado")
        self.tree.column("username", width=120)
        self.tree.column("nif", width=120)
        self.tree.column("nome", width=250)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # --- NOVO BLOCO: Arquivo Cloud / Local ---
        frm_arquivo = ttk.LabelFrame(self, text="Arquivo Seguro (Fotografias e PDFs)", padding=15)
        frm_arquivo.pack(fill=tk.X, pady=10)
        
        ttk.Label(frm_arquivo, text="Pasta Local Segura (Onde guardar permanentemente os ficheiros):").pack(anchor=tk.W, pady=(0, 5))
        
        frm_path = ttk.Frame(frm_arquivo)
        frm_path.pack(fill=tk.X, pady=(0, 5))
        
        self.var_path_arquivo = tk.StringVar()
        self.ent_path = ttk.Entry(frm_path, textvariable=self.var_path_arquivo, width=50)
        self.ent_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        btn_browse = ttk.Button(frm_path, text="Procurar...", command=self.browse_archive_path)
        btn_browse.pack(side=tk.LEFT)
        
        self.var_sincronizar_auto = tk.BooleanVar(value=False)
        self.chk_sync = ttk.Checkbutton(frm_arquivo, text="Ativar Cópia de Segurança Local Automática", variable=self.var_sincronizar_auto)
        self.chk_sync.pack(anchor=tk.W, pady=5)
        
        ttk.Label(frm_arquivo, text="Nota: A integração direta com Google Drive será adicionada brevemente através do 'Google Drive Desktop'.", font=("Segoe UI", 8, "italic")).pack(anchor=tk.W)
        
        # Botão Guardar
        btn_save = ttk.Button(self, text="💾 Guardar Definições", command=self.save_data, style="Accent.TButton")
        btn_save.pack(pady=20, ipady=5)
        
    def browse_archive_path(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Selecione a Pasta de Arquivo")
        if folder:
            self.var_path_arquivo.set(folder)
        
    def update_ui_state(self):
        tipo = self.var_tipo.get()
        if tipo == "Empresarial":
            self.frame_details.config(text="Dados da Empresa (Máximo 1 NIF)")
        else:
            self.frame_details.config(text="NIFs Autorizados (Agregado Familiar)")
            
    def load_data(self):
        db = get_session()
        try:
            definicao = db.query(DefinicoesPerfil).first()
            if definicao:
                self.var_tipo.set(definicao.tipo)
                if definicao.regime_iva:
                    self.var_regime.set(definicao.regime_iva)
                self.nifs_list = json.loads(definicao.nifs_associados)
                for item in self.nifs_list:
                    # Backward compatibility safely handled by `.get`
                    self.tree.insert("", tk.END, values=(item.get("username", "Empresa"), item.get("nif", ""), item.get("nome", "")))
                    
                # Load Archive settings
                if hasattr(definicao, 'caminho_arquivo_local') and definicao.caminho_arquivo_local:
                    self.var_path_arquivo.set(definicao.caminho_arquivo_local)
                if hasattr(definicao, 'sincronizar_auto'):
                    self.var_sincronizar_auto.set(definicao.sincronizar_auto)
                    
            self.update_ui_state()
            self.load_license_data()
        except Exception as e:
            print(f"Erro a carregar definições: {e}")
        finally:
            db.close()
            
    def add_nif(self):
        tipo = self.var_tipo.get()
        if tipo == "Empresarial" and len(self.tree.get_children()) >= 1:
            messagebox.showwarning("Aviso", "No modo empresarial, apenas 1 NIF Principal é permitido. Remova o atual primeiro.")
            return
            
        username = "Empresa"
        if tipo == "Pessoal":
            username = simpledialog.askstring("Novo Utilizador", "Nome de Utilizador/Alcunha (Ex: João):", parent=self)
            if not username: return
            username = username.strip()
            
        nif = simpledialog.askstring("Novo NIF", "Introduza o NIF (9 dígitos):", parent=self)
        if not nif: return
        nif = nif.replace(" ", "").strip()
        
        nome = simpledialog.askstring("Nome", "Qual o nome da pessoa / empresa associada a este NIF?", parent=self)
        if not nome: return
        nome = nome.strip()
        
        self.tree.insert("", tk.END, values=(username, nif, nome))
        
    def remove_nif(self):
        selected = self.tree.selection()
        if not selected:
            return
        self.tree.delete(selected[0])
        
    def save_data(self):
        db = get_session()
        try:
            definicao = db.query(DefinicoesPerfil).first()
            if not definicao:
                definicao = DefinicoesPerfil()
                db.add(definicao)
                
            definicao.tipo = self.var_tipo.get()
            definicao.regime_iva = self.var_regime.get()
            
            # Save Archive settings
            definicao.caminho_arquivo_local = self.var_path_arquivo.get()
            definicao.sincronizar_auto = self.var_sincronizar_auto.get()
            
            # Rebuild NIFS dict
            new_list = []
            for child in self.tree.get_children():
                username, nif, nome = self.tree.item(child)["values"]
                new_list.append({"username": str(username), "nif": str(nif), "nome": str(nome)})
                
            definicao.nifs_associados = json.dumps(new_list)
            
            db.commit()
            messagebox.showinfo("Sucesso", "Definições guardadas com sucesso!")
        except Exception as e:
            db.rollback()
            messagebox.showerror("Erro", f"Não foi possível guardar as definições: {e}")
        finally:
            db.close()

    def load_license_data(self):
        is_valid, msg = is_license_valid()
        if is_valid:
            try:
                with open(LICENSE_FILE, "r") as f:
                    license_key = f.read().strip()
                payload_b64 = license_key.split(".")[0]
                payload_str = base64.b64decode(payload_b64).decode()
                license_data = json.loads(payload_str)
                
                expire_date_str = license_data.get("expires")
                expire_date = datetime.datetime.strptime(expire_date_str, "%Y-%m-%d")
                dias_restantes = (expire_date - datetime.datetime.utcnow()).days
                
                self.lbl_days.config(text=f"{dias_restantes} dias ({expire_date_str})", foreground="green")
                
                ai_active = bool(license_data.get("ai_active", False))
                self.lbl_ai.config(text="✅ Ativo" if ai_active else "❌ Inativo", foreground="green" if ai_active else "red")
            except Exception as e:
                self.lbl_days.config(text="Erro ao ler validade", foreground="red")
                self.lbl_ai.config(text="--")
        else:
            self.lbl_days.config(text=f"Inválida ou Expirada: {msg}", foreground="red")
            self.lbl_ai.config(text="--")
            
    def update_license(self):
        new_key = self.entry_new_key.get().strip()
        if not new_key:
            messagebox.showwarning("Aviso", "Introduza uma nova chave de licença para atualizar.")
            return
            
        try:
            # Check validade sem a gravar ainda permanente (ou gravar e reverter?)
            # Para testar on-the-fly podemos verificar 
            temp_file = LICENSE_FILE + ".tmp"
            with open(temp_file, "w") as f:
                f.write(new_key)
                
            # Temporarily point is_license_valid ao temp_file? Não, a função está hardcoded.
            # Vamos substituir logo e se der erro pedimos a certa ou ficamos sem ela (menos mal)
            old_key = ""
            if os.path.exists(LICENSE_FILE):
                with open(LICENSE_FILE, "r") as f:
                    old_key = f.read()
                    
            with open(LICENSE_FILE, "w") as f:
                f.write(new_key)
            
            # Recarrega license feature globals if necessary
            is_valid, msg = is_license_valid()
            
            if is_valid:
                messagebox.showinfo("Sucesso", "Licença Validada e Atualizada com sucesso!\nA Inteligência Artificial ou novas features já estão ativas.")
                self.entry_new_key.delete(0, tk.END)
                self.load_license_data()
            else:
                # Revert
                with open(LICENSE_FILE, "w") as f:
                    f.write(old_key)
                messagebox.showerror("Erro de Licença", f"Rejeitada: {msg}\nCertifique-se que foi gerada para o seu Machine ID correto ou não expirou.")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro crítico: {str(e)}")
