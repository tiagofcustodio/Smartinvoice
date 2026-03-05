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

class Cliente(Base):
    """Clientes para quem os utilizadores emitem Faturas/Recibos."""
    __tablename__ = 'clientes'
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True, nullable=False)
    nif = Column(String, unique=True, index=True)
    morada = Column(String, nullable=True)
    email = Column(String, nullable=True)

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
    
    # Novos campos para Módulo Declaração IVA
    tipo_despesa = Column(String, default="Despesas da atividade") # "Despesas da atividade" ou "Despesas pessoais"
    grau_dedutibilidade = Column(Float, default=100.0) # Percentagem de dedução do IVA (Ex: 50.0 para Combustíveis)
    categoria_irs = Column(String) # Categoria para efeitos de IRS (Saúde, Educação, Gerais...)

    # Relacionamento de Reconciliação Bancária
    movimento_id = Column(Integer, ForeignKey('movimentos_bancarios.id'), nullable=True)

class ArtigoFatura(Base):
    """Artigos extraídos de uma fatura."""
    __tablename__ = 'artigos_fatura'
    
    id = Column(Integer, primary_key=True, index=True)
    fatura_id = Column(Integer, ForeignKey('faturas.id'))
    descricao = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    taxa_iva = Column(Float, default=0.0) # Taxa aplicada ex: 23.0, 13.0, 6.0, 0.0

class FaturaEmitida(Base):
    """Faturas emitidas pela entidade (Para SAF-T)."""
    __tablename__ = 'faturas_emitidas'
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    numero_fatura = Column(String, unique=True, index=True) # Ex: FT 2026/1
    data_emissao = Column(String) # YYYY-MM-DD
    total_liquido = Column(Float, nullable=False)
    total_imposto = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    estado = Column(String, default="Emitida") # Emitida, Anulada, Paga
    tipo_documento = Column(String, default="Fatura-Recibo") # Fatura, Fatura-Recibo, Recibo
    hash_saft = Column(String, nullable=True) # Assinatura digital do documento

class ArtigoFaturaEmitida(Base):
    """Linhas das faturas emitidas pela entidade."""
    __tablename__ = 'artigos_fatura_emitida'
    
    id = Column(Integer, primary_key=True, index=True)
    fatura_emitida_id = Column(Integer, ForeignKey('faturas_emitidas.id'))
    descricao = Column(String, nullable=False)
    quantidade = Column(Float, default=1.0)
    preco_unitario = Column(Float, nullable=False)
    taxa_iva = Column(Float, default=0.0)
    retencao_irs = Column(Float, default=0.0) # Permite gerir Recibos Verdes (Ex: 25.0)

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
    regime_iva = Column(String, default="Isento (Art. 53º)") # Isento (Art. 53º), Normal Trimestral, Normal Mensal
    at_nif = Column(String, default="")
    at_password = Column(String, default="")
    
    # Arquivo Cloud / Local Seguro
    caminho_arquivo_local = Column(String, default="") # Se "", usa a pasta normal
    google_drive_token = Column(String, default="") # Guardará o token oauth, se configurado
    sincronizar_auto = Column(Boolean, default=False)

class MovimentoBancario(Base):
    """Movimentos importados de um Extrato Bancário (CSV)."""
    __tablename__ = 'movimentos_bancarios'
    
    id = Column(Integer, primary_key=True, index=True)
    data = Column(String, nullable=False) # Guardar como ISO YYYY-MM-DD
    descricao = Column(String, nullable=False)
    valor = Column(Float, nullable=False) # Negativo = Débito/Despesa, Positivo = Crédito/Receita
    saldo = Column(Float, nullable=True)
    estado = Column(String, default="Pendente") # Pendente, Reconciliado, Ignorado
    
    # Faturas ligadas a este movimento
    faturas = relationship("Fatura", backref="movimento")
