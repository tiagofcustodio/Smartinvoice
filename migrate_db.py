import sqlite3
import os
import glob
from config import BASE_DIR

def migrate_database():
    db_files = glob.glob(os.path.join(BASE_DIR, "smartinvoice_*.db"))
    
    for db_path in db_files:
        print(f"Migrating database: {os.path.basename(db_path)}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Checking and adding columns to ArtigoFatura
        try:
            cursor.execute("ALTER TABLE artigos_fatura ADD COLUMN taxa_iva FLOAT DEFAULT 0.0")
            print(" - Added taxa_iva to artigos_fatura")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                print(f" - Error adding taxa_iva: {e}")
        
        # Checking and adding columns to Fatura
        try:
            cursor.execute("ALTER TABLE faturas ADD COLUMN tipo_despesa VARCHAR DEFAULT 'Despesas da atividade'")
            print(" - Added tipo_despesa to faturas")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                print(f" - Error adding tipo_despesa: {e}")
                
        try:
            cursor.execute("ALTER TABLE faturas ADD COLUMN grau_dedutibilidade FLOAT DEFAULT 100.0")
            print(" - Added grau_dedutibilidade to faturas")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                print(f" - Error adding grau_dedutibilidade: {e}")

        # Checking and adding columns to DefinicoesPerfil
        try:
            cursor.execute("ALTER TABLE definicoes_perfil ADD COLUMN regime_iva VARCHAR DEFAULT 'Isento (Art. 53º)'")
            print(" - Added regime_iva to definicoes_perfil")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                print(f" - Error adding regime_iva: {e}")
                
        conn.commit()
        conn.close()
        
if __name__ == "__main__":
    migrate_database()
