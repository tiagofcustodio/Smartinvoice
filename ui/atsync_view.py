import tkinter as tk
from tkinter import ttk, messagebox
import threading
from core.database import get_session
from core.models import DefinicoesPerfil
from core.at_connector import ATConnector

class ATSyncView(ttk.Frame):
    def __init__(self, parent, on_sync_finish=None):
        super().__init__(parent, padding=20)
        self.on_sync_finish = on_sync_finish
        self.connector = None
        self.setup_ui()
        self.load_credentials()
        
    def setup_ui(self):
        lbl_title = ttk.Label(self, text="☁️ Sincronização e-Fatura (AT)", font=("Segoe UI", 16, "bold"), foreground="#007ACC")
        lbl_title.pack(anchor=tk.W, pady=(0, 20))
        
        # Area de Info
        frm_info = ttk.Frame(self)
        frm_info.pack(fill=tk.X, pady=(0, 20))
        lbl_desc = ttk.Label(frm_info, text="Ligue-se diretamente ao serviço Webservice do Portal das Finanças para\ndescarregar automaticamente as faturas emitidas com o seu NIF como consumidor.", justify=tk.LEFT)
        lbl_desc.pack(anchor=tk.W)
        
        # Area de Login
        self.frm_login = ttk.LabelFrame(self, text="Credenciais de Acesso AT", padding=15)
        self.frm_login.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(self.frm_login, text="NIF (Acesso Portal):", width=20).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ent_nif = ttk.Entry(self.frm_login, width=30)
        self.ent_nif.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(self.frm_login, text="Palavra-Passe:", width=20).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ent_pwd = ttk.Entry(self.frm_login, width=30, show="*")
        self.ent_pwd.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        frm_actions = ttk.Frame(self.frm_login)
        frm_actions.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(15, 0))
        
        btn_save = ttk.Button(frm_actions, text="Guardar Credenciais", command=self.save_credentials)
        btn_save.pack(side=tk.LEFT, padx=(0, 10))
        
        # Autenticar
        self.btn_auth = ttk.Button(frm_actions, text="⟲ Testar Ligação", command=self.test_connection, style="Accent.TButton")
        self.btn_auth.pack(side=tk.LEFT)
        
        # Area Sincronização
        self.frm_sync = ttk.LabelFrame(self, text="Operações de Sincronização", padding=15)
        self.frm_sync.pack(fill=tk.X)
        self.frm_sync.pack_forget() # Hide initially
        
        ttk.Label(self.frm_sync, text="Descobrir faturas registadas no e-Fatura dos últimos:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cb_dias = ttk.Combobox(self.frm_sync, values=["30 Dias", "60 Dias", "90 Dias", "Este Ano"], state="readonly", width=15)
        self.cb_dias.set("30 Dias")
        self.cb_dias.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        self.btn_sync = ttk.Button(self.frm_sync, text="⬇️ Iniciar Sincronização (Download)", command=self.start_sync, style="Accent.TButton")
        self.btn_sync.grid(row=1, column=0, columnspan=2, pady=(15, 0), sticky=tk.W)
        
        self.lbl_status = ttk.Label(self.frm_sync, text="", font=("Segoe UI", 10, "italic"))
        self.lbl_status.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)
        
    def load_credentials(self):
        db = get_session()
        try:
            def_perfil = db.query(DefinicoesPerfil).first()
            if def_perfil:
                if def_perfil.at_nif:
                    self.ent_nif.insert(0, def_perfil.at_nif)
                if def_perfil.at_password:
                    self.ent_pwd.insert(0, def_perfil.at_password)
        except Exception:
            pass
        finally:
            db.close()
            
    def save_credentials(self):
        db = get_session()
        try:
            def_perfil = db.query(DefinicoesPerfil).first()
            if not def_perfil:
                def_perfil = DefinicoesPerfil()
                db.add(def_perfil)
                
            def_perfil.at_nif = self.ent_nif.get().strip()
            def_perfil.at_password = self.ent_pwd.get().strip()
            db.commit()
            messagebox.showinfo("Sucesso", "Credenciais guardadas com sucesso no perfil.")
        except Exception as e:
            messagebox.showerror("Erro BD", str(e))
        finally:
            db.close()
            
    def test_connection(self):
        nif = self.ent_nif.get().strip()
        pwd = self.ent_pwd.get().strip()
        
        if not nif or not pwd:
            messagebox.showwarning("Aviso", "Preencha o NIF e Palavra-passe antes de ligar.")
            return
            
        self.btn_auth.config(state=tk.DISABLED, text="A Autenticar...")
        self.update()
        
        # Logica Mock AT
        self.connector = ATConnector(nif, pwd)
        success, msg = self.connector.authenticate()
        
        self.btn_auth.config(state=tk.NORMAL, text="⟲ Testar Ligação")
        
        if success:
            messagebox.showinfo("Sucesso", msg)
            self.frm_sync.pack(fill=tk.X) # Mostra painel de sync
        else:
            messagebox.showerror("Acesso Negado", msg)
            self.frm_sync.pack_forget()
            
    def start_sync(self):
        self.btn_sync.config(state=tk.DISABLED)
        self.lbl_status.config(text="A descarregar dados do servidor e-Fatura...", foreground="blue")
        threading.Thread(target=self._run_sync_thread, daemon=True).start()
        
    def _run_sync_thread(self):
        try:
            success, result = self.connector.fetch_recent_invoices(days=30)
            if success:
                faturas = result
                n_fats = len(faturas)
                self.lbl_status.config(text=f"Sincronização concluída! Foram detetadas {n_fats} fatura(s) novas.", foreground="green")
                
                # Import automatic to DB (Mocking logic to show on table)
                self.import_to_db(faturas)
                
                if self.on_sync_finish:
                    self.after(0, self.on_sync_finish)
            else:
                self.lbl_status.config(text=f"Erro na Sincronização: {result}", foreground="red")
        except Exception as e:
            self.lbl_status.config(text="Erro crítico no WebService.", foreground="red")
        finally:
            self.btn_sync.config(state=tk.NORMAL)
            
    def import_to_db(self, faturas):
        # We need to simulate the injection into our DB just like OCR does
        db = get_session()
        from core.models import Fornecedor, Fatura
        try:
            for f_data in faturas:
                nif_fn = f_data["nifEmitente"]
                nome_fn = f_data["nomeEmitente"]
                
                fn = db.query(Fornecedor).filter(Fornecedor.nif == nif_fn).first()
                if not fn:
                    fn = Fornecedor(nome=nome_fn, nif=nif_fn)
                    db.add(fn)
                    db.flush()
                    
                nova_fatura = Fatura(
                    fornecedor_id=fn.id,
                    data=f_data["dataDocumento"],
                    total=float(f_data["totalDocumento"]),
                    estado="Sincronizada (AT)",
                    tipo_despesa="Despesas pessoais",
                    categoria_irs=f_data["setor"],
                    grau_dedutibilidade=100.0
                )
                db.add(nova_fatura)
            db.commit()
        except Exception as e:
            print("Erro a injetar na BD", str(e))
        finally:
            db.close()
