import tkinter as tk
from tkinter import ttk, messagebox
import os
from license.validator import is_license_valid, LICENSE_FILE
from license.license_manager import get_machine_id

class LicenseWindow:
    def __init__(self, root, on_success_callback):
        self.root = root
        self.on_success_callback = on_success_callback
        
        self.root.title("SmartInvoice - Ativação Necessária")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        # Center window
        self.root.eval('tk::PlaceWindow . center')
        
        self.machine_id = get_machine_id()
        self.setup_ui()
        
    def setup_ui(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        lbl_title = ttk.Label(frame, text="Ativação do Produto", font=("Helvetica", 14, "bold"))
        lbl_title.pack(pady=(0, 10))
        
        lbl_desc = ttk.Label(frame, text="Para utilizar o SmartInvoice, por favor ative a sua licença.\nEnvie o Machine ID abaixo para o suporte para obter a chave.", justify=tk.CENTER)
        lbl_desc.pack(pady=5)
        
        # Frame for machine ID
        mid_frame = ttk.Frame(frame)
        mid_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(mid_frame, text="Machine ID:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W)
        self.entry_mid = ttk.Entry(mid_frame, font=("Courier", 12))
        self.entry_mid.insert(0, self.machine_id)
        self.entry_mid.config(state="readonly")
        self.entry_mid.pack(fill=tk.X, pady=5)
        
        btn_copy = ttk.Button(mid_frame, text="Copiar Machine ID", command=self.copy_mid)
        btn_copy.pack(anchor=tk.E)
        
        # Key Entry
        ttk.Label(frame, text="Chave de Ativação:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W, pady=(15, 0))
        self.text_key = tk.Text(frame, height=4, font=("Courier", 10))
        self.text_key.pack(fill=tk.X, pady=5)
        
        # Action Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=15)
        
        btn_activate = ttk.Button(btn_frame, text="OK - Ativar Licença", command=self.activate)
        btn_activate.pack(side=tk.RIGHT, padx=5, ipady=5, ipadx=10)
        
        btn_exit = ttk.Button(btn_frame, text="Sair", command=self.root.quit)
        btn_exit.pack(side=tk.RIGHT, ipady=5)
        
        # Permitir pressionar o "Enter" na caixa da chave para ativar
        self.root.bind('<Return>', lambda event: self.activate())
        
    def copy_mid(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.machine_id)
        messagebox.showinfo("Copiado", "Machine ID copiado para a área de transferência.")
        
    def activate(self):
        key = self.text_key.get("1.0", tk.END).strip()
        if not key:
            messagebox.showerror("Erro", "Por favor introduza a chave de ativação.")
            return
            
        try:
            with open(LICENSE_FILE, "w") as f:
                f.write(key)
                
            is_valid, msg = is_license_valid()
            if is_valid:
                messagebox.showinfo("Sucesso", "Licença ativada com sucesso!")
                self.on_success_callback()
            else:
                os.remove(LICENSE_FILE) # Remove invalid key
                messagebox.showerror("Erro de Ativação", msg)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao guardar a licença: {str(e)}")
