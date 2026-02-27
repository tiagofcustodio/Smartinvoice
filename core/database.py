from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from config import BASE_DIR

# Globals to hold the engine and session factory dynamically
engine = None
SessionLocal = None
Base = declarative_base()

def setup_database(profile_name="default"):
    """
    Inicializa a Base de Dados dinamicamente com base no perfil escolhido.
    Cria ficheiros como 'empresaA.db', 'pessoal.db'.
    """
    global engine, SessionLocal
    
    db_filename = f"smartinvoice_{profile_name}.db"
    db_path = os.path.join(BASE_DIR, db_filename)
    db_uri = f"sqlite:///{db_path}"
    
    engine = create_engine(db_uri, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Criar tabelas se não existirem
    import core.models
    Base.metadata.create_all(bind=engine)
        
def get_session():
    if not SessionLocal:
        setup_database("default")
    return SessionLocal()
        
def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()

