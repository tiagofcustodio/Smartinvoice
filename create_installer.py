import sys
import os
import zipfile
import subprocess
import shutil

DIST_DIR = "dist"
PAYLOAD_ZIP = "payload.zip"
INSTALLER_STUB = "setup_stub.py"

def create_payload():
    """Zips the contents of the `dist/app` folder into a single archive."""
    print("A compilar os binários da app num ficheiro unificado (payload.zip)...")
    app_dir = os.path.join(DIST_DIR, "app")
    with zipfile.ZipFile(PAYLOAD_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(app_dir):
            for root, dirs, files in os.walk(app_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    # The archive name should preserve the internal folder structure 'app/...'
                    arcname = os.path.join("app", os.path.relpath(filepath, app_dir))
                    zf.write(filepath, arcname)

def build_installer_exe():
    """Generates the installer script and compiles it with PyInstaller."""
    print("A gerar o executável final de instalação (SmartInvoice_Setup.exe)...")
    
    installer_code = """
import os
import sys
import zipfile
import subprocess
import tkinter as tk
from tkinter import messagebox

def create_shortcut(target, shortcut_path, icon=None):
    # Using PowerShell to create a shortcut (.lnk)
    try:
        ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target}"
$Shortcut.Save()
'''
        subprocess.run(["powershell", "-Command", ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        print(f"Erro ao criar atalho: {e}")

def main():
    root = tk.Tk()
    root.withdraw() # Hide the main window
    
    # Bundle folder in PyInstaller --onefile
    bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    payload_path = os.path.join(bundle_dir, "payload.zip")
    
    if not os.path.exists(payload_path):
        messagebox.showerror("Erro de Instalação", "O ficheiro de instalação (payload) está corrompido ou ausente!")
        return

    # Install Directory (e.g. C:\\Users\\Name\\AppData\\Local\\SmartInvoice)
    install_dir = os.path.join(os.environ["LOCALAPPDATA"], "SmartInvoice")
    os.makedirs(install_dir, exist_ok=True)
    
    try:
        # Extract payload
        with zipfile.ZipFile(payload_path, 'r') as zf:
            zf.extractall(install_dir)
            
        # Create Desktop Shortcuts
        desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
        
        # SmartInvoice App
        app_exe = os.path.join(install_dir, "app", "SmartInvoice.exe")
        shortcut_path = os.path.join(desktop, "SmartInvoice.lnk")
        if os.path.exists(app_exe):
            create_shortcut(app_exe, shortcut_path)
            
        messagebox.showinfo(
            "SmartInvoice", 
            f"✅ A instalação foi concluída com sucesso!\\n\\n"
            f"O programa foi instalado na tua pasta pessoal (sem necessitar de privilégios de Admin).\\n"
            f"Foi criado um atalho no Ambiente de Trabalho."
        )
    except Exception as e:
        messagebox.showerror("Erro Crítico", f"Ocorreu um problema ao extrair a aplicação.\\n\\n{str(e)}")

if __name__ == '__main__':
    main()
"""
    with open(INSTALLER_STUB, "w", encoding="utf-8") as f:
        f.write(installer_code)
        
    cmd = [
        "pyinstaller", 
        "--noconfirm", 
        "--onefile", 
        "--windowed",
        "--name=SmartInvoice_Setup",
        f"--add-data={PAYLOAD_ZIP};.",
        INSTALLER_STUB
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Sucesso: Instalador final compilado.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao compilar o instalador:\\n{e}")
        exit(1)

def cleanup():
    """Removes temporary build files."""
    for item in [PAYLOAD_ZIP, INSTALLER_STUB, "SmartInvoice_Setup.spec"]:
        if os.path.exists(item):
            os.remove(item)

if __name__ == '__main__':
    print("Iniciando o pacote de distribuição do SmartInvoice (Instalador final)...")
    create_payload()
    build_installer_exe()
    cleanup()
    print("\\n[OK] O Instalador final 'SmartInvoice_Setup.exe' foi criado na pasta 'dist/'.")
