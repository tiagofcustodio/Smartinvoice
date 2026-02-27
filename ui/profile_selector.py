import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import os
import glob
import json
from typing import Any
from config import BASE_DIR

class ProfileSelector(tk.Toplevel):
    def __init__(self, parent, on_profile_selected):
        super().__init__(parent)
        self.on_profile_selected = on_profile_selected
        
        self.title("SmartInvoice - Selecionar Perfil / Empresa")
        self.geometry("400x300")
        self.resizable(False, False)
        
        self.val_profile: Any = None
        self.cb_profiles: Any = None
        
        # Ocultar a janela root nativa que fica por trás enquanto isto flutua
        self.parent = parent
        self.parent.withdraw()
        
        # Centrar no ecrã usando a parent root
        self.tk.eval(f'tk::PlaceWindow {str(self)} center')
        
        # Interceptar fecho no X para encerrar a app inteira
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.setup_ui()
        
    def setup_ui(self):
        frm = ttk.Frame(self, padding=20)
        frm.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frm, text="Bem-vindo ao SmartInvoice", font=("Helvetica", 14, "bold")).pack(pady=(0, 20))
        
        ttk.Label(frm, text="Selecione o perfil ou empresa a carregar:").pack(anchor=tk.W)
        
        self.val_profile = tk.StringVar()
        self.cb_profiles = ttk.Combobox(frm, textvariable=self.val_profile, state="readonly", font=("Helvetica", 11))
        self.cb_profiles.pack(fill=tk.X, pady=10, ipady=3)
        
        self.refresh_profiles()
        
        btn_frame = ttk.Frame(frm)
        btn_frame.pack(fill=tk.X, pady=20)
        
        btn_enter = ttk.Button(btn_frame, text="✅ Iniciar", command=self.do_select, style="Accent.TButton")
        btn_enter.pack(side=tk.RIGHT, padx=5, ipady=5, ipadx=10)
        
        btn_new = ttk.Button(btn_frame, text="➕ Novo Perfil", command=self.do_new, style="Accent.TButton")
        btn_new.pack(side=tk.LEFT, padx=5, ipady=5)
        
        btn_delete = ttk.Button(btn_frame, text="🗑️ Eliminar", command=self.do_delete)
        btn_delete.pack(side=tk.LEFT, padx=5, ipady=5)
        
    def refresh_profiles(self):
        # Procura por smartinvoice_*.db no BASE_DIR
        pattern = os.path.join(BASE_DIR, "smartinvoice_*.db")
        db_files = glob.glob(pattern)
        
        perfis = []
        for f in db_files:
            basename = os.path.basename(f)
            # Remove "smartinvoice_" e ".db"
            name = basename.replace("smartinvoice_", "").replace(".db", "")
            perfis.append(name)
            
        if not perfis:
            perfis = ["default"]
            
        self.cb_profiles['values'] = perfis
        self.cb_profiles.set(perfis[0])
        
    def do_new(self):
        wizard = NewProfileWizard(self)
        self.wait_window(wizard)
        if wizard.created_profile:
            self.val_profile.set(wizard.created_profile)
            self.do_select()
                
    def do_select(self):
        prof = self.val_profile.get()
        if not prof:
            messagebox.showwarning("Aviso", "Selecione um perfil.")
            return
            
        self.destroy() # Fechar popup
        self.parent.deiconify() # Revelar o root do tkinter para que o main.py reconstrua o Dashboard em cima dele
        self.on_profile_selected(prof)
        
    def do_delete(self):
        prof = self.val_profile.get()
        if not prof:
            messagebox.showwarning("Aviso", "Selecione o perfil que pretende eliminar.")
            return
            
        if prof == "default":
            messagebox.showwarning("Aviso", "O perfil 'default' não pode ser eliminado desta forma.")
            return
            
        resposta = messagebox.askyesno(
            "Eliminar Perfil", 
            f"Tem a certeza ABSOLUTA que pretende eliminar o perfil '{prof}'?\n\nTODAS as faturas, fornecedores e configurações associadas a este perfil serão PERDIDAS IRREVERSIVELMENTE."
        )
        
        if resposta:
            try:
                db_path = os.path.join(BASE_DIR, f"smartinvoice_{prof}.db")
                if os.path.exists(db_path):
                    os.remove(db_path)
                    messagebox.showinfo("Sucesso", f"Perfil '{prof}' eliminado com sucesso.")
                    self.refresh_profiles()
                else:
                    messagebox.showerror("Erro", "O ficheiro da base de dados não foi encontrado.")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível eliminar o perfil:\n{str(e)}")
                
    def on_close(self):
        self.parent.destroy() # Mata app inteira

class NewProfileWizard(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Criar Novo Perfil")
        self.geometry("550x500")
        self.resizable(False, False)
        self.created_profile: Any = None
        
        self.entry_dbname: Any = None
        self.var_tipo: Any = None
        self.frm_details: Any = None
        self.frm_domestic: Any = None
        self.tree_users: Any = None
        self.frm_business: Any = None
        self.entry_bus_nif: Any = None
        self.entry_bus_name: Any = None
        
        # Center the wizard over the ProfileSelector
        # Removido transient/grab_set para evitar bloqueios ao criar o Toplevel
        self.update_idletasks()
        
        # Center manually
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        self.geometry(f"+{parent_x + 50}+{parent_y + 50}")
        
        self.setup_ui()
        
    def setup_ui(self):
        frm = ttk.Frame(self, padding=20)
        frm.pack(fill=tk.BOTH, expand=True)
        
        # Profile Name (DB File)
        ttk.Label(frm, text="1. Identificação do Perfil", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(frm, text="Nome da base de dados (Ex: 'familia', 'pastelaria'):").pack(anchor=tk.W)
        self.entry_dbname = ttk.Entry(frm, width=30)
        self.entry_dbname.pack(fill=tk.X, pady=(0, 15), ipady=4)
        
        # Profile Type
        ttk.Label(frm, text="2. Tipo de Perfil", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        self.var_tipo = tk.StringVar(value="Pessoal")
        
        frm_tipos = ttk.Frame(frm)
        frm_tipos.pack(fill=tk.X, pady=(0, 10))
        ttk.Radiobutton(frm_tipos, text="Doméstico (Agregado Familiar)", variable=self.var_tipo, value="Pessoal", command=self.update_view).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(frm_tipos, text="Empresarial", variable=self.var_tipo, value="Empresarial", command=self.update_view).pack(side=tk.LEFT)
        
        # Details Frame dynamically changing
        self.frm_details = ttk.LabelFrame(frm, text="Dados Fiscais (NIFs associados)", padding=10)
        self.frm_details.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # For Domestic
        self.frm_domestic = ttk.Frame(self.frm_details)
        # Table of users
        cols = ("username", "nif", "nome")
        self.tree_users = ttk.Treeview(self.frm_domestic, columns=cols, show="headings", height=4)
        self.tree_users.heading("username", text="Utilizador")
        self.tree_users.heading("nif", text="NIF")
        self.tree_users.heading("nome", text="Nome Completo")
        self.tree_users.column("username", width=120)
        self.tree_users.column("nif", width=100)
        self.tree_users.column("nome", width=200)
        self.tree_users.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        btn_add_dom = ttk.Button(self.frm_domestic, text="+ Adicionar Utilizador", command=self.add_domestic_user, style="Accent.TButton")
        btn_add_dom.pack(side=tk.RIGHT)
        
        # For Business
        self.frm_business = ttk.Frame(self.frm_details)
        ttk.Label(self.frm_business, text="NIF da Empresa:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.entry_bus_nif = ttk.Entry(self.frm_business, width=20)
        self.entry_bus_nif.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(self.frm_business, text="Nome da Empresa:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entry_bus_name = ttk.Entry(self.frm_business, width=40)
        self.entry_bus_name.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Button Area
        btn_cri = ttk.Button(self, text="💾 Criar Perfil e Iniciar", command=self.create_profile_db, style="Accent.TButton")
        btn_cri.pack(pady=10, ipady=6)
        
        self.update_view()
        
    def update_view(self):
        tipo = self.var_tipo.get()
        if tipo == "Pessoal":
            self.frm_business.pack_forget()
            self.frm_domestic.pack(fill=tk.BOTH, expand=True)
            self.frm_details.config(text="Dados do Agregado Familiar (NIFs para faturas)")
        else:
            self.frm_domestic.pack_forget()
            self.frm_business.pack(fill=tk.BOTH, expand=True)
            self.frm_details.config(text="Dados Oficiais da Empresa")
            
    def add_domestic_user(self):
        username = simpledialog.askstring("Novo Utilizador", "Nome de Utilizador/Alcunha (Ex: João):", parent=self)
        if not username: return
        nif = simpledialog.askstring("Novo Utilizador", f"NIF para as faturas de {username} (9 dígitos):", parent=self)
        if not nif: return
        nome = simpledialog.askstring("Novo Utilizador", f"Nome Próprio associado a este NIF nas faturas:", parent=self)
        if not nome: return
        
        self.tree_users.insert("", tk.END, values=(username.strip(), nif.strip(), nome.strip()))
        
    def create_profile_db(self):
        db_raw_name = self.entry_dbname.get().strip()
        if not db_raw_name:
            messagebox.showwarning("Aviso", "Tem de introduzir um nome para o Perfil (base de dados).")
            return
            
        db_safe = "".join(x for x in db_raw_name if x.isalnum() or x in "-_").lower()
        if len(db_safe) < 2:
            messagebox.showwarning("Aviso", "Nome de perfil inválido (ex: use 'empresaA').")
            return
            
        tipo = self.var_tipo.get()
        nifs_data = [] # JSON list to save
        
        if tipo == "Pessoal":
            if not self.tree_users.get_children():
                messagebox.showwarning("Aviso", "Adicione pelo menos 1 Utilizador e respetivo NIF.")
                return
            for child in self.tree_users.get_children():
                # returns tuple (username, nif, nome)
                vals = self.tree_users.item(child)["values"]
                nifs_data.append({"username": str(vals[0]), "nif": str(vals[1]), "nome": str(vals[2])})
        else:
            # Empresarial
            nif = self.entry_bus_nif.get().strip()
            nome = self.entry_bus_name.get().strip()
            if not nif or not nome:
                messagebox.showwarning("Aviso", "Preencha o NIF e o Nome da Empresa.")
                return
            nifs_data.append({"username": "Empresa", "nif": nif, "nome": nome})
            
        # Write to Database
        try:
            from core.database import setup_database, get_session
            from core.models import DefinicoesPerfil
            
            # This instantiates engine, SessionLocal, and runs create_all()
            setup_database(db_safe) 
            db = get_session()
            
            # Wipe definitions just in case it existed
            db.query(DefinicoesPerfil).delete()
            
            nova_def = DefinicoesPerfil(
                tipo=tipo,
                nome_principal=db_safe,
                nifs_associados=json.dumps(nifs_data)
            )
            db.add(nova_def)
            db.commit()
            db.close()
            
            self.created_profile = db_safe
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro Fatal", f"Ocorreu um erro a gerar a base de dados: {str(e)}")
