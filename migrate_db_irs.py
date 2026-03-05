import sqlite3
import os
import glob
from config import BASE_DIR

def run_migration():
    pattern = os.path.join(BASE_DIR, "smartinvoice_*.db")
    db_files = glob.glob(pattern)
    
    print(f"Encontradas {len(db_files)} bases de dados para migrar.")
    
    for db_path in db_files:
        try:
            print(f"A verificar {os.path.basename(db_path)}...")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if `categoria_irs` exists in `faturas`
            cursor.execute("PRAGMA table_info(faturas)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "categoria_irs" not in columns:
                print(" -> A adicionar coluna 'categoria_irs' em faturas...")
                # Assume default as Despesas Gerais Familiares for past invoices
                cursor.execute("ALTER TABLE faturas ADD COLUMN categoria_irs VARCHAR DEFAULT 'Despesas Gerais Familiares'")
            else:
                print(" -> Coluna 'categoria_irs' já existe.")
                
            conn.commit()
            conn.close()
            print(" -> Migração concluída com sucesso.\n")
        except Exception as e:
            print(f" -> Erro ao migrar {os.path.basename(db_path)}: {e}")

if __name__ == "__main__":
    run_migration()
