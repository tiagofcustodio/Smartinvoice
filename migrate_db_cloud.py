import sqlite3
import os
import glob
from config import BASE_DIR

def run_migration():
    pattern = os.path.join(BASE_DIR, "smartinvoice_*.db")
    db_files = glob.glob(pattern)
    
    print(f"Encontradas {len(db_files)} bases de dados para migrar (Arquivo Cloud / Local).")
    
    for db_path in db_files:
        try:
            print(f"A verificar {os.path.basename(db_path)}...")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Adicionar colunas cloud à tabela definicoes_perfil se não existirem
            cursor.execute("PRAGMA table_info(definicoes_perfil)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "caminho_arquivo_local" not in columns:
                print(" -> A adicionar coluna 'caminho_arquivo_local' em definicoes_perfil...")
                cursor.execute("ALTER TABLE definicoes_perfil ADD COLUMN caminho_arquivo_local VARCHAR DEFAULT ''")
                
            if "google_drive_token" not in columns:
                print(" -> A adicionar coluna 'google_drive_token' em definicoes_perfil...")
                cursor.execute("ALTER TABLE definicoes_perfil ADD COLUMN google_drive_token VARCHAR DEFAULT ''")
                
            if "sincronizar_auto" not in columns:
                print(" -> A adicionar coluna 'sincronizar_auto' em definicoes_perfil...")
                cursor.execute("ALTER TABLE definicoes_perfil ADD COLUMN sincronizar_auto BOOLEAN DEFAULT 0")
                
            conn.commit()
            conn.close()
            print(" -> Migração concluída com sucesso.\n")
        except Exception as e:
            print(f" -> Erro ao migrar {os.path.basename(db_path)}: {e}")

if __name__ == "__main__":
    run_migration()
