import sqlite3
import os
import glob
from config import BASE_DIR

def run_migration():
    pattern = os.path.join(BASE_DIR, "smartinvoice_*.db")
    db_files = glob.glob(pattern)
    
    print(f"Encontradas {len(db_files)} bases de dados para migrar (Emissão de Faturas).")
    
    for db_path in db_files:
        try:
            print(f"A verificar {os.path.basename(db_path)}...")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Criar tabela clientes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome VARCHAR NOT NULL,
                    nif VARCHAR UNIQUE,
                    morada VARCHAR,
                    email VARCHAR
                )
            """)
            
            # Criar tabela faturas_emitidas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS faturas_emitidas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER REFERENCES clientes(id),
                    numero_fatura VARCHAR UNIQUE,
                    data_emissao VARCHAR,
                    total_liquido FLOAT NOT NULL,
                    total_imposto FLOAT NOT NULL,
                    total FLOAT NOT NULL,
                    estado VARCHAR DEFAULT 'Emitida',
                    tipo_documento VARCHAR DEFAULT 'Fatura-Recibo',
                    hash_saft VARCHAR
                )
            """)
            
            # Criar tabela artigos_fatura_emitida
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS artigos_fatura_emitida (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fatura_emitida_id INTEGER REFERENCES faturas_emitidas(id),
                    descricao VARCHAR NOT NULL,
                    quantidade FLOAT DEFAULT 1.0,
                    preco_unitario FLOAT NOT NULL,
                    taxa_iva FLOAT DEFAULT 0.0,
                    retencao_irs FLOAT DEFAULT 0.0
                )
            """)

            conn.commit()
            conn.close()
            print(" -> Migração concluída com sucesso.\n")
        except Exception as e:
            print(f" -> Erro ao migrar {os.path.basename(db_path)}: {e}")

if __name__ == "__main__":
    run_migration()
