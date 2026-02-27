import sys
import threading
import tkinter as tk
from tkinter import ttk

from config import PENDING_DIR, PROCESSED_DIR
import os
from license.validator import is_license_valid
from ui.license_window import LicenseWindow
from ui.dashboard import Dashboard
from ui.profile_selector import ProfileSelector
from webserver.server import start_server
from core.email_fetcher import start_email_service_thread
from core.database import setup_database
import threading
import sv_ttk
import darkdetect

def ensure_directories():
    """Garante que as pastas necessárias existem."""
    for d in [PENDING_DIR, PROCESSED_DIR]:
        os.makedirs(d, exist_ok=True)

def start_main_app(root, profile_name="default"):
    # Clear root se esteve na página da licença
    for widget in root.winfo_children():
        widget.destroy()
        
    root.title(f"SmartInvoice - Dashboard Contabilístico [{profile_name}]")
    root.geometry("1000x600")
        
    app = Dashboard(root, profile_name=profile_name)

def main():
    ensure_directories()
    
    root = tk.Tk()
    
    # Inicia a app sempre em fullscreen / maximizada (funciona bem em Windows)
    try:
        root.state('zoomed')
    except tk.TclError:
        # Fallback para outros SOs se 'zoomed' não for suportado
        root.attributes('-zoomed', True)
    
    # Aplicar o Tema "Sun Valley" (Windows 11 Native Look) ao Tkinter - Forçar Tema Claro
    sys_theme = darkdetect.theme()
    sv_ttk.set_theme("light")
    
    # Check License
    is_valid, msg = is_license_valid()
    
    def boot_core_services_and_ui(profile_name):
        # 1. Preparar DB para este Perfil (Multi-Tenant)
        setup_database(profile_name)
        
        # 2. Iniciar Serviços Secundários
        web_thread = threading.Thread(target=start_server, daemon=True)
        web_thread.start()
        start_email_service_thread()
        
        # 3. Arrancar a UI Principal do Dashboard
        start_main_app(root, profile_name)
        
    def run_profile_selector():
        # Antes de iniciar, pedimos o login de empresa
        ProfileSelector(root, boot_core_services_and_ui)
        
    if is_valid:
        run_profile_selector()
    else:
        # Abre janela de licenciamento e só se sucesso abre o resto
        LicenseWindow(root, run_profile_selector)
        
    root.mainloop()
    
    # === SHUTDOWN SEQUENCE ===
    print("A encerrar SmartInvoice. A criar backup automático de segurança...")
    from core.backup_manager import create_local_backup
    create_local_backup()
    print("Até à Próxima!")

if __name__ == "__main__":
    main()
