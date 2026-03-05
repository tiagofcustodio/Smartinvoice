import requests
import json
from datetime import datetime

class ATConnector:
    """
    Simula uma ligação ao Webservice e-Fatura da AT (Autoridade Tributária).
    Na realidade, a AT não fornece uma API REST pública para os cidadãos descarregarem os seus próprios ficheiros sem ser por via do webservice SOAP SAF-T ou web scraping do portal das finanças, o que exigiria um certificado de Software ou as credenciais completas do utilizador em texto limpo.
    Para os efeitos deste software MVP/Simulador empresarial, iremos disponibilizar a moldura de autenticação e comunicação para um sistema que o suporte.
    """
    
    BASE_URL = "https://servicos.portaldasfinancas.gov.pt/efatura/"
    
    def __init__(self, nif, password):
        self.nif = nif
        self.password = password
        self.session = requests.Session()
        self.is_authenticated = False
        self.auth_token = None
        
    def authenticate(self):
        """
        Simulador de Autenticação OAuth2 / Autenticação.gov para comunicação AT direta.
        Em ambiente de produção real, envolveria OAuth, CMD (Chave Móvel Digital) ou Web Scraping com Puppeteer/Selenium se a API não estiver aberta ao cidadão.
        """
        try:
            # Em simulação, vamos apenas validar se o NIF é credível
            if not self.nif or len(str(self.nif)) != 9:
                return False, "NIF inválido para autenticação AT."
                
            if not self.password:
                return False, "A Palavra-Passe do Portal das Finanças é obrigatória."
            
            # Simulated Success
            self.is_authenticated = True
            self.auth_token = "SIMULATED_AT_TOKEN_2026"
            return True, "Autenticado com sucesso no Portal das Finanças."
            
        except Exception as e:
            return False, f"Erro de ligação à AT: {str(e)}"
            
    def fetch_recent_invoices(self, days=30):
        """
        Saca a lista de faturas comunicadas no E-fatura como Adquirente.
        """
        if not self.is_authenticated:
            return False, "Sessão AT não inicializada ou expirada."
            
        # Numa API real, faríamos um GET a um endpoint de aquisições:
        # url = f"{self.BASE_URL}aquisicoes?dias={days}"
        # headers = {"Authorization": f"Bearer {self.auth_token}"}
        # ...
        
        # Simulação de resposta AT (Como se fosse a AT a devolver dados JSON)
        return True, [
            {
                "nifEmitente": "500222111",
                "nomeEmitente": "Vodafone Portugal, S.A.",
                "dataDocumento": datetime.now().strftime("%Y-%m-%d"),
                "totalDocumento": "45.99",
                "totalIva": "10.58",
                "estadoFatura": "REGISTADA",
                "setor": "Comunicações"
            },
            {
                "nifEmitente": "505666777",
                "nomeEmitente": "Galp Energia, S.A.",
                "dataDocumento": datetime.now().strftime("%Y-%m-%d"),
                "totalDocumento": "65.00",
                "totalIva": "12.15",
                "estadoFatura": "REGISTADA",
                "setor": "Combustíveis"
            }
        ]
