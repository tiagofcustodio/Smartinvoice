import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser

from config import APP_VERSION
from core.updater import check_for_updates

class HomeView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.setup_ui()
        self.check_update_status()
        
    def setup_ui(self):
        # Header
        lbl_welcome = ttk.Label(self, text="Bem-vindo ao SmartInvoice", font=("Segoe UI", 24, "bold"), foreground="#007ACC")
        lbl_welcome.pack(anchor=tk.W, pady=(0, 5))
        
        lbl_desc = ttk.Label(self, text="O seu assistente inteligente para gestão e extração de faturas.", font=("Segoe UI", 12))
        lbl_desc.pack(anchor=tk.W, pady=(0, 20))
        
        # Grid para Cards
        grid_frame = ttk.Frame(self)
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Card 1: Informações do Sistema ---
        card_info = ttk.LabelFrame(grid_frame, text="Informação do Sistema")
        card_info.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        ttk.Label(card_info, text="Versão Atual:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Label(card_info, text=APP_VERSION).grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(card_info, text="Módulo IA (Gemini):", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        # Mostrar o Status Dinâmico do Módulo IA consoante a licença local
        self.lbl_ai_status = ttk.Label(card_info, text="A verificar...")
        self.lbl_ai_status.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        self.check_license_features()
        
        # --- Card 2: Atualizações ---
        self.card_updates = ttk.LabelFrame(grid_frame, text="Atualizações de Software")
        self.card_updates.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.lbl_update_status = ttk.Label(self.card_updates, text="A procurar atualizações...", font=("Segoe UI", 11))
        self.lbl_update_status.pack(pady=20, padx=10)
        
        self.update_details_frame = ttk.Frame(self.card_updates)
        self.lbl_release_notes = ttk.Label(self.update_details_frame, text="", wraplength=300)
        self.btn_download = ttk.Button(self.update_details_frame, text="Descarregar Atualização", style="Accent.TButton")
        
        # Configurar peso da grid para que os cards fiquem do mesmo tamanho
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

    def check_license_features(self):
        try:
            from license.validator import get_license_features
            features = get_license_features()
            if features.get("ai_active", False):
                self.lbl_ai_status.config(text="✅ Ativo", foreground="green")
            else:
                self.lbl_ai_status.config(text="❌ Inativo", foreground="red")
        except:
             self.lbl_ai_status.config(text="Erro ao verificar lincença")

    def check_update_status(self):
        def worker():
            has_update, latest_v, url, notes = check_for_updates()
            # Precisamos de usar o .after para chamar código da UI de volta na Main Thread do Tkinter
            self.after(0, lambda: self.update_ui_with_results(has_update, latest_v, url, notes))
            
        threading.Thread(target=worker, daemon=True).start()
        
    def update_ui_with_results(self, has_update, latest_v, url, notes):
        if has_update:
            self.lbl_update_status.config(text=f"🥳 Nova versão disponível: v{latest_v}\n(A sua versão: v{APP_VERSION})", foreground="#d97706")
            
            self.update_details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self.lbl_release_notes.config(text=f"Novidades:\n{notes}")
            self.lbl_release_notes.pack(anchor=tk.W, pady=5)
            
            self.btn_download.config(command=lambda: webbrowser.open(url))
            self.btn_download.pack(pady=10, ipady=5)
        else:
            self.lbl_update_status.config(text="✅ A sua aplicação está atualizada!", foreground="green")
            self.update_details_frame.pack_forget()
