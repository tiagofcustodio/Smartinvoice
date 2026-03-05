import os
import subprocess
import shutil

# Nomes dos executáveis e diretórios
APP_SCRIPT = "main.py"
APP_NAME = "SmartInvoice"
ADMIN_SCRIPT = "license_admin.py"
ADMIN_NAME = "SmartInvoice_Admin"

DIST_DIR = "dist"
APP_DIST_DIR = os.path.join(DIST_DIR, "app")
ADMIN_DIST_DIR = os.path.join(DIST_DIR, "admin")

def run_pyinstaller(script_path, exe_name, output_dir, is_windowed=True, icon_path=None):
    """Executa o PyInstaller com os argumentos apropriados"""
    print(f"\n--- A compilar {exe_name} ---")
    
    cmd = [
        "pyinstaller",
        "--noconfirm",         # Substituir output anterior sem perguntar
        "--onedir",            # Criar pasta c/ dependências (mais rápido a abrir que onefile)
        f"--name={exe_name}",  # Nome do executável
        f"--distpath={output_dir}", # Pasta de destino
        "--hidden-import=pkg_resources._vendor.jaraco.text",
        "--hidden-import=pkg_resources._vendor.jaraco.functools",
        "--hidden-import=pkg_resources._vendor.jaraco.context",
        "--hidden-import=jaraco.text",
        "--hidden-import=jaraco.functools",
        "--hidden-import=jaraco.context"
    ]
    
    if is_windowed:
        cmd.append("--windowed")  # Não abrir a consola preta por trás do Tkinter
        
    if icon_path and os.path.exists(icon_path):
        cmd.append(f"--icon={icon_path}")
        
    cmd.append(script_path)
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Sucesso: {exe_name} compilado para {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao compilar {exe_name}. Detalhes:\n{e}")
        exit(1)

def post_build_cleanup():
    """Limpa ficheiros residuais da compilação e copia tesseract"""
    print("\n--- Limpeza e Preparação Final ---")
    
    # Apagar pastas temporárias do PyInstaller
    for p in ["build", f"{APP_NAME}.spec", f"{ADMIN_NAME}.spec"]:
        if os.path.exists(p):
            if os.path.isdir(p):
                shutil.rmtree(p)
            else:
                os.remove(p)
                
    # Copiar Tesseract Installer para a pasta principal da app se existir
    tesseract_installer = "tesseract-installer.exe"
    if os.path.exists(tesseract_installer):
        dest_tesseract = os.path.join(APP_DIST_DIR, APP_NAME, tesseract_installer)
        shutil.copy2(tesseract_installer, dest_tesseract)
        print(f"Tesseract Installer copiado para {dest_tesseract}")
        
    # Copiar o Tesseract Data atual (por.traineddata) se existir
    tessdata_path = os.path.join("tessdata", "por.traineddata")
    if os.path.exists(tessdata_path):
        dest_tessdata_folder = os.path.join(APP_DIST_DIR, APP_NAME, "tessdata")
        os.makedirs(dest_tessdata_folder, exist_ok=True)
        shutil.copy2(tessdata_path, os.path.join(dest_tessdata_folder, "por.traineddata"))
        print(f"Dados PTP/Tesseract copiados para a distribuição.")

if __name__ == "__main__":
    print("Iniciando o processo de Build do SmartInvoice...")
    
    # 1. Compilar App Principal (Windowed)
    run_pyinstaller(APP_SCRIPT, APP_NAME, APP_DIST_DIR, is_windowed=True)
    
    # 2. Compilar Admin Tool (Console Misto/Windowed)
    run_pyinstaller(ADMIN_SCRIPT, ADMIN_NAME, ADMIN_DIST_DIR, is_windowed=True)
    
    # 3. Mover ficheiros e limpar
    post_build_cleanup()
    
    print("\nBuild concluído! Verifique a pasta 'dist/' no seu projeto.")
