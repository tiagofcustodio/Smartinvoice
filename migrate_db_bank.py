import sqlite3
import os
import glob
from config import BASE_DIR

def run_migration():
    pattern = os.path.join(BASE_DIR, "smartinvoice_*.db")
    db_files = glob.glob(pattern)
    
    print(f"Encontradas {len(db_files)} bases de dados para migrar (Reconciliação Bancária).")
    
    for db_path in db_files:
        try:
            print(f"A verificar {os.path.basename(db_path)}...")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Criar tabela movimentos_bancarios se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimentos_bancarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data VARCHAR NOT NULL,
                    descricao VARCHAR NOT NULL,
                    valor FLOAT NOT NULL,
                    saldo FLOAT,
                    estado VARCHAR DEFAULT 'Pendente'
                )
            """)
            
            # Adicionar coluna movimento_id à tabela faturas se não existir
            cursor.execute("PRAGMA table_info(faturas)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "movimento_id" not in columns:
                print(" -> A adicionar coluna 'movimento_id' em faturas...")
                try:
                    cursor.execute("ALTER TABLE faturas ADD COLUMN movimento_id INTEGER REFERENCES movimentos_bancarios(id)")
                except Exception as e:
                    print(f" -> Aviso ao adicionar FK: {e}")
            else:
                print(" -> Coluna 'movimento_id' já existe em faturas.")
                
            conn.commit()
            conn.close()
            print(" -> Migração concluída com sucesso.\n")
        except Exception as e:
            print(f" -> Erro ao migrar {os.path.basename(db_path)}: {e}")

if __name__ == "__main__":
    run_migration()
