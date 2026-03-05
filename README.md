# SmartInvoice 🧾

O **SmartInvoice** é uma aplicação desktop inteligente desenvolvida em Python para gestão de despesas, organização contabilística e extração automatizada de dados a partir de fotografias e PDFs de faturas ou talões portugueses.

Concebido para automatizar a vida a contabilistas, empresas e utilizadores domésticos que não querem perder tempo a inserir dados à mão.

---

## ✨ Funcionalidades Principais

* **Extração Inteligente por IA (Gemini 2.5 Flash):** O coração do sistema. Lê recibos enrugados, fotografias escuras e talões de supermercado. Extrai NIF, Data, Total, Fornecedor e todos os **Artigos** lado a lado com os valores. Tudo automaticamente sem que o utilizador mova um dedo.
* **Fallback para OCR Offline:** Mecanismo secundário de leitura utilizando o Tesseract OCR (gratuito e local) para caso não exista uma subscrição IA ativa. Tem inteligência lexical própria (classificador automático) de modo a sugerir ao utilizador o modelo preditivo para classificar uma despesa.
* **Validação de Fornecedores VIES:** Se o sistema encontrou um NIF na fatura e não sabe o nome da empresa, ou o nome é ilegível, liga-se silenciosamente à AT/VIES da União Europeia a fim de popular corretamente a designação fiscal da empresa de imediato.
* **Envios Segundos do Telemóvel:** Nada de cabos. A aplicação gera um *QR Code* contendo um servidor local Wi-Fi. O utilizador aponta o ecrã do telemóvel para o PC, abre a câmara e as faturas "voam" imediatamente para dentro do computador prontas a processar.
* **Dashboard e Relatórios Mensais:** Análise em tempo real onde o dinheiro foi gasto agrupado em categorias contabilísticas (Supermercados, Combustíveis, Saúde, Equipamentos, Telecomunicações).
* **Gestor de Perfis Rigoroso:** Divide a casa da empresa. Crie múltiplas bases de dados consoante a "Entidade" selecionada, impedindo falsos-positivos na classificação de emitentes e adquirentes (A IA é impedida proativamente de considerar a sua empresa como um prestador de serviços caso o seu logótipo apareça).
* **Auto-Atualizador (Auto-Updater):** Ligado diretamente à API do GitHub, avisa imediatamente o utilizador dentro do painel do Windows caso saia uma versão nova para descarregar contendo as notas de patch.
* **Sistema de Licenciamento Criptográfico:** Acompanhado de uma ferramenta utilitária e ultra-segura *(SmartInvoice_Admin)* fechada aos clientes que utiliza chaves validadas de hardware para permitir ou bloquear acessos. 

---

## 🛠️ Tecnologias Utilizadas

A aplicação junta potentes bibliotecas da linguagem Python e modelos na núvem:

- **Tkinter (Visuals)** - Modernizado, rápido e de base nativa para a UI.
- **SQLAlchemy & SQLite** - Robustez relacional infalível no armazenamento de contas offline.
- **Google Generative AI** - O cérebro cognitivo multimodal encarregue da digitalização de inteligência.
- **PyTesseract** - Leitura algorítmica de pixéis local/offline.
- **Flask & Socket** - Host na receção super leve de transferências Wi-Fi Mobile -> PC.
- **Matplotlib** - Para a geração de relatórios gráficos de piza no painel de controlo.
- **PyInstaller** - Compilação binária.

---

## 🚀 Como Executar Localmente na sua Máquina (Dev)

Certifique-se de que tem o Python 3.12 instalado.

1. **Clone o repositório:**
    ```bash
    git clone https://github.com/tiagofcustodio/Smartinvoice.git
    cd Smartinvoice
    ```

2. **Crie um ambiente virtual e ative-o:**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3. **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Variáveis e Senhas de Ambiente:**
    Crie um ficheiro `gemini.key` ou adicione uma variável de sistema `GOOGLE_API_KEY` com a sua key do Gemini Studio para as features online da AI funcionarem.

5. **Inicie o projeto:**
    ```bash
    python main.py
    ```

*(Nota: O Tesseract OCR precisa de possuir as bibliotecas linguísticas de português treinadas (`por.traineddata`).*

---

## 📦 Exportação para Produção (Build Portable)

Quer enviar o produto final para um cliente fechado?

Corra o script de compilação local construído explicitamente para tratar de todo o peso atrelado:

```bash
python build_dist.py
```
*(O script cuida da exclusão de rastos de desenvolvimento, cópia de linguagens do Tesseract, remoção de ficheiros vazios e cria perfeitamente duas pastas `.exe` portáteis, para o administrador e para o cliente final, sob a pasta `./dist`).*

---

### Licença e Direitos
Criado à medida para escalar e revolucionar o tratamento processual de secretária moderno.
