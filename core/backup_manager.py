import os
import zipfile
import datetime
import glob
from config import BASE_DIR, UPLOADS_DIR

BACKUPS_DIR = os.path.join(BASE_DIR, "backups")

def create_local_backup():
    """
    Comprime todas as bases de dados e a pasta de faturas num ficheiro ZIP selado.
    Isto garante salvaguarda contra corrupção local.
    """
    if not os.path.exists(BACKUPS_DIR):
        os.makedirs(BACKUPS_DIR, exist_ok=True)
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUPS_DIR, f"SmartInvoice_Backup_{timestamp}.zip")
    
    print(f"A criar backup de segurança em: {backup_file}")
    
    try:
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 1. Adicionar todas as base de dados
            db_files = glob.glob(os.path.join(BASE_DIR, "*.db"))
            for db_path in db_files:
                if os.path.exists(db_path):
                    zipf.write(db_path, arcname=os.path.basename(db_path))
                    
            # 2. Adicionar as Imagens Físicas
            if os.path.exists(UPLOADS_DIR):
                for root, dirs, files in os.walk(UPLOADS_DIR):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Caminho relativo dentro do zip
                        arcname = os.path.join("uploads", os.path.relpath(file_path, UPLOADS_DIR))
                        zipf.write(file_path, arcname=arcname)
                        
        print("Backup concluído com sucesso!")
        return True, backup_file
    except Exception as e:
        print(f"Erro ao criar backup: {str(e)}")
        return False, str(e)
