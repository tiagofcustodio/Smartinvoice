import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import shutil
# sv_ttk handled in main.py, do not import here to avoid circular/missing issues
from ui.home_view import HomeView
from ui.upload_view import UploadView
from ui.invoices_view import InvoicesView
from ui.monthly_view import MonthlyView
from ui.settings_view import SettingsView
from config import PENDING_DIR, PROCESSED_DIR, MOBILE_APP_TOKEN
from ocr.ocr_engine import extract_text
from ocr.parser import parse_invoice_text
from ocr.gemini_engine import extract_structured_data_with_gemini
from core.ml_classifier import guess_supplier_and_category
from core.database import get_session
from core.models import Fatura, Fornecedor, Categoria, ArtigoFatura
from license.validator import get_license_features
from core.nif_validator import validate_nif_vies


class Dashboard(ttk.Frame):
    def __init__(self, parent, profile_name="default"):
        super().__init__(parent)
        self.parent = parent
        self.profile_name = profile_name
        self.pack(fill=tk.BOTH, expand=True)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Sidebar menu
        self.sidebar_frame = ttk.Frame(self, width=220)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10,0), pady=10)
        
        lbl_menu = ttk.Label(self.sidebar_frame, text="SmartInvoice", font=("Segoe UI", 16, "bold"), foreground="#007ACC")
        lbl_menu.pack(pady=(20, 5), padx=10)
        
        lbl_profile = ttk.Label(self.sidebar_frame, text=f"👤 Perfil: {self.profile_name.capitalize()}", font=("Segoe UI", 10))
        lbl_profile.pack(pady=(0, 20), padx=10)
        
        # Botões de navegação
        self.btn_bg = "#f5f5f5"
        self.btn_fg = "#333333"
        self.act_bg = "#e0e0e0"
        self.font_nav = ("Segoe UI", 11)

        self.btn_home = tk.Button(self.sidebar_frame, text="🏠 Início", command=self.show_home, font=self.font_nav, bg=self.btn_bg, fg=self.btn_fg, activebackground=self.act_bg, relief="flat", cursor="hand2", anchor="w", padx=20)
        self.btn_home.pack(fill=tk.X, padx=10, pady=5, ipady=6)
        
        self.btn_upload = tk.Button(self.sidebar_frame, text="🖨️ Digitalizar", command=self.show_upload, font=self.font_nav, bg=self.btn_bg, fg=self.btn_fg, activebackground=self.act_bg, relief="flat", cursor="hand2", anchor="w", padx=20)
        self.btn_upload.pack(fill=tk.X, padx=10, pady=5, ipady=6)
        
        self.btn_faturas = tk.Button(self.sidebar_frame, text="📑 Faturas", command=self.show_faturas, font=self.font_nav, bg=self.btn_bg, fg=self.btn_fg, activebackground=self.act_bg, relief="flat", cursor="hand2", anchor="w", padx=20)
        self.btn_faturas.pack(fill=tk.X, padx=10, pady=5, ipady=6)
        
        self.btn_resumo = tk.Button(self.sidebar_frame, text="📊 Resumo Mensal", command=self.show_resumo, font=self.font_nav, bg=self.btn_bg, fg=self.btn_fg, activebackground=self.act_bg, relief="flat", cursor="hand2", anchor="w", padx=20)
        self.btn_resumo.pack(fill=tk.X, padx=10, pady=5, ipady=6)
        
        self.btn_mobile = tk.Button(self.sidebar_frame, text="📱 Telemóvel", command=self.show_mobile_instructions, font=self.font_nav, bg=self.btn_bg, fg=self.btn_fg, activebackground=self.act_bg, relief="flat", cursor="hand2", anchor="w", padx=20)
        self.btn_mobile.pack(fill=tk.X, padx=10, pady=5, ipady=6)
        
        self.btn_settings = tk.Button(self.sidebar_frame, text="⚙️ Definições", command=self.show_settings, font=self.font_nav, bg=self.btn_bg, fg=self.btn_fg, activebackground=self.act_bg, relief="flat", cursor="hand2", anchor="w", padx=20)
        self.btn_settings.pack(fill=tk.X, padx=10, pady=5, ipady=6)
        
        lbl_status = ttk.Label(self.sidebar_frame, text="🟢 Web Server Ativo", justify=tk.CENTER, foreground="green")
        lbl_status.pack(side=tk.BOTTOM, pady=20)
        
        # Separator Line
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # Main content area
        self.content_frame = ttk.Frame(self, padding=20)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        # Init views
        self.views = {
            "home": HomeView(self.content_frame),
            "upload": UploadView(self.content_frame, self),
            "faturas": InvoicesView(self.content_frame),
            "resumo": MonthlyView(self.content_frame),
            "settings": SettingsView(self.content_frame)
        }
        
        # Start with Home View
        self.show_home()
        
        # Iniciar verificação da pasta de uploads
        self.check_pending_uploads()
        
    def check_pending_uploads(self):
        """Verifica se há ficheiros novos em /uploads/pending/ a cada 5 segundos"""
        if not hasattr(self, "_processing_files"):
            self._processing_files = set()
            import threading
            self.threading = threading

        try:
            for filename in os.listdir(PENDING_DIR):
                filepath = os.path.join(PENDING_DIR, filename)
                if os.path.isfile(filepath) and filename not in self._processing_files:
                    self._processing_files.add(filename)
                    # Executa a extração OCR/AI numa thread separada para não bloquear a UI (App Lenta)
                    self.threading.Thread(target=self.process_invoice_thread, args=(filepath, filename), daemon=True).start()
        except Exception as e:
            print(f"Erro ao verificar uploads: {e}")
            
        # Repete a verificação a cada 5 segundos
        self.after(5000, self.check_pending_uploads)
        
    def process_invoice_thread(self, filepath, filename):
        """Wrapper que limpa o ficheiro da lista de processamento quando terminar"""
        try:
            self.process_invoice(filepath, filename)
        finally:
            if filename in self._processing_files:
                self._processing_files.remove(filename)
        
    def process_invoice(self, filepath, filename):
        """Processa a imagem com OCR, classifica e insere na BD"""
        try:
            # Check local license for AI Module
            features = get_license_features()
            ai_active = features.get("ai_active", False)
            
            if ai_active:
                print("Iniciando extração via Gemini AI...")
                parsed_data = extract_structured_data_with_gemini(filepath)
                sugerido_nome = parsed_data.get("fornecedor_nome", "Desconhecido")
                sugerido_cat_nome = parsed_data.get("categoria", "Outros")
                if not sugerido_cat_nome: sugerido_cat_nome = "Outros"
                if not sugerido_nome: sugerido_nome = "Desconhecido"
            else:
                print("Iniciando extração via Tesseract Local (Offline)...")
                # 1. OCR Local
                text = extract_text(filepath)
                
                # 2. Parsing Local (NIF, Data, Total)
                parsed_data = parse_invoice_text(text)
                
                # 3. Classificação Local
                sugerido_nome, sugerido_cat_nome = guess_supplier_and_category(text)
            
            # Validate if chosen name matches the current profile names to avoid assigning own company as supplier
            db_check = get_session()
            from core.models import DefinicoesPerfil
            import json
            try:
                def_perfil = db_check.query(DefinicoesPerfil).first()
                if def_perfil and def_perfil.nifs_associados:
                    perf_nomes = [item.get("nome", "").lower() for item in json.loads(def_perfil.nifs_associados) if item.get("nome")]
                    if sugerido_nome.lower() in perf_nomes:
                        sugerido_nome = "Desconhecido"
            except Exception:
                pass
            finally:
                db_check.close()
            
            # Se a inteligência (Local ou AI) não conhecer o Fornecedor, a UI pediria ajuda, mas estamos numa thread de bg
            # O utilizador vai poder editar e classificar na janela de edição aberta automaticamente.
            if sugerido_nome == "Desconhecido":
                sugerido_cat_nome = "Outros"
            
            # 4. BD Logic
            db = get_session()
            
            # Verificar/Criar Fornecedor
            nif_extracted = parsed_data.get("nif", "")
            fornecedor = None
            
            if nif_extracted:
                fornecedor = db.query(Fornecedor).filter(Fornecedor.nif == nif_extracted).first()
                
            if not fornecedor:
                fornecedor = db.query(Fornecedor).filter(Fornecedor.nome == sugerido_nome).first()
                
            if not fornecedor:
                # Validar NIF no VIES para obter nome oficial e exato da empresa se possível
                if nif_extracted and len(str(nif_extracted)) >= 9:
                    is_valid, vies_name, _ = validate_nif_vies(nif_extracted)
                    if is_valid and vies_name != "Desconhecido":
                        print(f"VIES: Nome '{sugerido_nome}' corrigido pelo Estado para Oficial '{vies_name}'")
                        sugerido_nome = vies_name
                        
                fornecedor = Fornecedor(nome=sugerido_nome, nif=nif_extracted)
                db.add(fornecedor)
                db.commit()
                db.refresh(fornecedor)
                
            # Verificar/Criar Categoria
            categoria = db.query(Categoria).filter(Categoria.nome == sugerido_cat_nome).first()
            if not categoria:
                categoria = Categoria(nome=sugerido_cat_nome, conta_debito_codigo="62")
                db.add(categoria)
                db.commit()
                db.refresh(categoria)
                
            # Criar Fatura
            fatura = Fatura(
                fornecedor_id=fornecedor.id,
                data=parsed_data["data"],
                total=parsed_data["total"] if parsed_data["total"] else 0.0,
                categoria_id=categoria.id,
                estado="Pendente"
            )
            db.add(fatura)
            db.commit()
            db.refresh(fatura)
            
            # Inserir Artigos da fatura
            for art in parsed_data.get("artigos", []):
                novo_artigo = ArtigoFatura(
                    fatura_id=fatura.id,
                    descricao=art["descricao"],
                    valor=art["valor"]
                )
                db.add(novo_artigo)
                
            db.commit()
            
            # Guardamos o ID antes de fechar a sessão para evitar DetachedInstanceError
            fatura_id = fatura.id
            db.close()
            
            # Mover ficheiro
            dest_path = os.path.join(PROCESSED_DIR, filename)
            shutil.move(filepath, dest_path)
            
            # Atualizar Tabela (se visível) - Tem de ser no main thread
            if self.views["faturas"].winfo_ismapped():
                self.after(0, self.views["faturas"].load_data)
                
            # Abrir logo a edição/revisão da Fatura para o utilizador confirmar os valores extraídos
            self.after(0, lambda: self.views["faturas"].edit_invoice(fatura_id))
            
        except Exception as e:
            messagebox.showerror("Erro de Processamento", f"Falha ao processar {filename}: {str(e)}")
            # Mover para erro ou similar, por agora ignora / repete

    def _hide_all_views(self):
        for view in self.views.values():
            view.grid_forget()
            
    def _set_active_button(self, active_btn):
        # Reset all standard buttons to inactive style
        buttons = [self.btn_home, self.btn_upload, self.btn_faturas, self.btn_resumo, self.btn_mobile, self.btn_settings]
        for btn in buttons:
            btn.configure(bg=self.btn_bg, fg=self.btn_fg)
            
        # Highlight the active button with primary color
        if active_btn:
            active_btn.configure(bg="#007ACC", fg="white")
            
    def show_home(self):
        self._hide_all_views()
        self._set_active_button(self.btn_home)
        self.views["home"].grid(row=0, column=0, sticky="nsew")
        
    def show_upload(self):
        self._hide_all_views()
        self._set_active_button(self.btn_upload)
        self.views["upload"].grid(row=0, column=0, sticky="nsew")
        
    def show_faturas(self):
        self._hide_all_views()
        self._set_active_button(self.btn_faturas)
        self.views["faturas"].load_data()  # Atualiza os dados
        self.views["faturas"].grid(row=0, column=0, sticky="nsew")
        
    def show_resumo(self):
        self._hide_all_views()
        self._set_active_button(self.btn_resumo)
        self.views["resumo"].refresh_months_list()
        self.views["resumo"].load_data()
        self.views["resumo"].grid(row=0, column=0, sticky="nsew")
        
    def show_settings(self):
        self._hide_all_views()
        self._set_active_button(self.btn_settings)
        self.views["settings"].load_data()
        self.views["settings"].grid(row=0, column=0, sticky="nsew")
        
    def show_mobile_instructions(self):
        self._set_active_button(self.btn_mobile)
        # Janela de ajuda para a ligação ao Telemóvel
        top = tk.Toplevel(self)
        top.title("Como ligar o Telemóvel")
        top.geometry("500x550")
        top.transient(self.winfo_toplevel())
        top.grab_set()
        
        # Apply modern theme frame
        main_frame = ttk.Frame(top, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        lbl_h1 = ttk.Label(main_frame, text="Conectar Dispositivo Móvel", font=("Helvetica", 16, "bold"))
        lbl_h1.pack(pady=(0, 10))
        
        lbl_desc = ttk.Label(
            main_frame, 
            text="1. Certifique-se que o telemóvel e o PC estão na mesma rede Wi-Fi.\n2. Aponte a câmara para o QR Code abaixo\n3. Autorizar na Firewall no primeiro acesso, se pedido.", 
            justify=tk.CENTER,
            font=("Helvetica", 10)
        )
        lbl_desc.pack(pady=(0, 15))
        
        # Obter IP primário
        import socket
        ip_primary = "127.0.0.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_primary = s.getsockname()[0]
            s.close()
        except Exception:
            pass

        # Obter todos os IPs para mostrar alternativas se falhar o primário
        all_ips = []
        try:
            hostname = socket.gethostname()
            all_ips = [ip for ip in socket.gethostbyname_ex(hostname)[2] if not ip.startswith("127.")]
        except Exception:
            pass

        url_local = f"http://{ip_primary}:5000/?token={MOBILE_APP_TOKEN}"
        
        lbl_url = ttk.Label(main_frame, text=f"Endereço Principal: {url_local}", font=("Helvetica", 12, "bold"), foreground="#007ACC")
        lbl_url.pack(pady=5)
        
        # Gerar o QRCode do IP primário
        try:
            import qrcode
            from PIL import ImageTk, Image
            
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(url_local)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            img = img.resize((220, 220), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)
            
            lbl_qr = ttk.Label(main_frame, image=img_tk)
            lbl_qr.image = img_tk
            lbl_qr.pack(pady=15)
        except ImportError:
            lbl_no_qr = ttk.Label(main_frame, text="(Módulo 'qrcode' em falta. Use o endereço acima no browser)", foreground="red")
            lbl_no_qr.pack(pady=20)
            
        # Mostrar endereços alternativos
        alt_ips = [ip for ip in all_ips if ip != ip_primary]
        if alt_ips:
            alt_frame = ttk.LabelFrame(main_frame, text="Se o principal não funcionar, tente:")
            alt_frame.pack(fill=tk.X, pady=10, ipady=5)
            for ip in alt_ips:
                alt_url = f"http://{ip}:5000/?token={MOBILE_APP_TOKEN}"
                ttk.Label(alt_frame, text=alt_url, font=("Helvetica", 10)).pack(pady=2)

        btn_close = ttk.Button(main_frame, text="Voltar ao Dashboard", command=top.destroy)
        btn_close.pack(pady=(15, 0))

    def ask_for_classification(self, filename, text):
        """Abre um pop-up a pedir ao utilizador para classificar o Fornecedor não reconhecido"""
        # Criamos uma janela bloqueante (Toplevel) customizada em vez do simpledialog para pedir 2 coisas
        dialog = tk.Toplevel(self)
        dialog.title("Novo Fornecedor Encontrado")
        dialog.geometry("450x300")
        dialog.transient(self.winfo_toplevel()) 
        dialog.grab_set() 
        
        # Variáveis para guardar o resultado
        res = {"nome": "Desconhecido", "cat": "Outros"}
        
        lbl = ttk.Label(dialog, text=f"O SmartInvoice não reconheceu a loja da fatura '{filename}'\n\nPor favor, introduza os dados para ensinar o sistema:", justify=tk.CENTER)
        lbl.pack(pady=20, padx=10)
        
        # Nome Fornecedor
        frm_nome = ttk.Frame(dialog)
        frm_nome.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(frm_nome, text="Nome do Fornecedor:", width=20).pack(side=tk.LEFT)
        ent_nome = ttk.Entry(frm_nome)
        ent_nome.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Categoria
        frm_cat = ttk.Frame(dialog)
        frm_cat.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(frm_cat, text="Categoria Contabilística:", width=20).pack(side=tk.LEFT)
        cb_cat = ttk.Combobox(frm_cat, values=["Supermercado", "Combustível", "Material Elétrico", "Materiais Construção", "Restaurante", "Telecomunicações", "Equipamento", "Outros"])
        cb_cat.set("Outros")
        cb_cat.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def save():
            n = ent_nome.get().strip()
            if n: res["nome"] = n
            res["cat"] = cb_cat.get()
            dialog.destroy()
            
        def ignore():
            dialog.destroy()
            
        btn_frm = ttk.Frame(dialog)
        btn_frm.pack(fill=tk.X, pady=20)
        ttk.Button(btn_frm, text="Gravar e Aprender", command=save).pack(side=tk.RIGHT, padx=20)
        ttk.Button(btn_frm, text="Ignorar (Fica Desconhecido)", command=ignore).pack(side=tk.RIGHT)
        
        self.wait_window(dialog)
        return res["nome"], res["cat"]

