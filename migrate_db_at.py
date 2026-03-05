import sqlite3
import os
import glob
from config import BASE_DIR

def run_migration():
    pattern = os.path.join(BASE_DIR, "smartinvoice_*.db")
    db_files = glob.glob(pattern)
    
    print(f"Encontradas {len(db_files)} bases de dados para migrar (AT).")
    
    for db_path in db_files:
        try:
            print(f"A verificar {os.path.basename(db_path)}...")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if `at_nif` exists in `definicoes_perfil`
            cursor.execute("PRAGMA table_info(definicoes_perfil)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "at_nif" not in columns:
                print(" -> A adicionar colunas 'at_nif' e 'at_password' em definicoes_perfil...")
                cursor.execute("ALTER TABLE definicoes_perfil ADD COLUMN at_nif VARCHAR DEFAULT ''")
                cursor.execute("ALTER TABLE definicoes_perfil ADD COLUMN at_password VARCHAR DEFAULT ''")
            else:
                print(" -> Colunas AT já existem.")
                
            conn.commit()
            conn.close()
            print(" -> Migração concluída com sucesso.\n")
        except Exception as e:
            print(f" -> Erro ao migrar {os.path.basename(db_path)}: {e}")

if __name__ == "__main__":
    run_migration()
