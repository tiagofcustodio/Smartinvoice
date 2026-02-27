import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
from config import PENDING_DIR

class UploadView(ttk.Frame):
    def __init__(self, parent, on_upload_success=None):
        super().__init__(parent, padding=20)
        self.on_upload_success = on_upload_success
        self.setup_ui()
        
    def setup_ui(self):
        lbl_title = ttk.Label(self, text="Upload de Faturas", font=("Segoe UI", 20, "bold"), foreground="#007ACC")
        lbl_title.pack(pady=(0, 20))
        
        lbl_desc = ttk.Label(self, text="Selecione os ficheiros (PDF, JPG, PNG) para digitalizar e processar.", justify=tk.CENTER, font=("Segoe UI", 12))
        lbl_desc.pack(pady=10)
        
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Segoe UI", 12, "bold"))
        
        btn_upload = ttk.Button(self, text="📁 Selecionar Faturas do PC", command=self.select_files, style="Accent.TButton")
        btn_upload.pack(pady=30, ipadx=20, ipady=10)
        
        lbl_info = ttk.Label(self, text="Também pode utilizar o seu telemóvel acedendo à mesma rede\ne enviando a foto diretamente para este ecrã.", foreground="gray", justify=tk.CENTER, font=("Segoe UI", 10))
        lbl_info.pack(pady=20)
        
    def select_files(self):
        filetypes = (
            ('Imagens e PDFs', '*.pdf *.jpg *.jpeg *.png'),
            ('Todos os ficheiros', '*.*')
        )
        
        filepaths = filedialog.askopenfilenames(
            title="Selecione as Faturas",
            filetypes=filetypes
        )
        
        if filepaths:
            try:
                count = 0
                for filepath in filepaths:
                    filename = os.path.basename(filepath)
                    dest_path = os.path.join(PENDING_DIR, filename)
                    shutil.copy2(filepath, dest_path)
                    count += 1
                messagebox.showinfo("Sucesso", f"{count} Fatura(s) enviada(s) para a fila de processamento!")
                if self.on_upload_success:
                    if hasattr(self.on_upload_success, 'show_faturas'):
                        self.on_upload_success.show_faturas()
                    else:
                        self.on_upload_success()
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível copiar os ficheiros: {str(e)}")
