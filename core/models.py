from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
import datetime
from core.database import Base

class PlanoContas(Base):
    """Plano oficial de contas contabilísticas."""
    __tablename__ = 'plano_contas'
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=False) # Ex: 624, 11
    descricao = Column(String, nullable=False)
    tipo = Column(String) # Ativo, Passivo, Gasto, Rendimento

class Categoria(Base):
    """Categorias para classificação inteligente."""
    __tablename__ = 'categorias'
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True, nullable=False) # Ex: Combustível
    conta_debito_codigo = Column(String, ForeignKey('plano_contas.codigo'))

class Fornecedor(Base):
    """Fornecedores lidos pelas faturas."""
    __tablename__ = 'fornecedores'
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True, nullable=False)
    nif = Column(String, unique=True, index=True)
    categoria_default_id = Column(Integer, ForeignKey('categorias.id'), nullable=True) # ML simplificado

class Fatura(Base):
    """Faturas validadas do OCR."""
    __tablename__ = 'faturas'
    
    id = Column(Integer, primary_key=True, index=True)
    fornecedor_id = Column(Integer, ForeignKey('fornecedores.id'))
    data = Column(String) # Guardar como ISO YYYY-MM-DD
    total = Column(Float, nullable=False)
    categoria_id = Column(Integer, ForeignKey('categorias.id'), nullable=True)
    estado = Column(String, default="Pendente") # Pendente, Contabilizada
    caminho_ficheiro = Column(String, nullable=True)

class ArtigoFatura(Base):
    """Artigos extraídos de uma fatura."""
    __tablename__ = 'artigos_fatura'
    
    id = Column(Integer, primary_key=True, index=True)
    fatura_id = Column(Integer, ForeignKey('faturas.id'))
    descricao = Column(String, nullable=False)
    valor = Column(Float, nullable=False)

class Lancamento(Base):
    """Lançamentos gerados."""
    __tablename__ = 'lancamentos'
    
    id = Column(Integer, primary_key=True, index=True)
    fatura_id = Column(Integer, ForeignKey('faturas.id'))
    conta_debito = Column(String, nullable=False)
    conta_credito = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    data_lancamento = Column(DateTime, default=datetime.datetime.utcnow)

class DefinicoesPerfil(Base):
    """Configuração de Perfil (Pessoal/Empresarial) com lista de NIFs válidos."""
    __tablename__ = 'definicoes_perfil'
    
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, default="Pessoal") # Pessoal ou Empresarial
    nome_principal = Column(String, nullable=True) 
    # Guarda um JSON stringificado ex: [{"nif": "123", "nome": "Pai"}, {"nif": "456", "nome": "Mãe"}]
    # ou para empresa: [{"nif": "500", "nome": "A Minha Empresa Lda"}]
    nifs_associados = Column(String, default="[]")
