import tkinter as tk
from tkinter import ttk, messagebox
from core.database import get_session
from core.models import Fatura, Fornecedor, Categoria, ArtigoFatura, Lancamento
from accounting.lancamentos import gerar_lancamento_automatico
from saft.saft_export import export_saft_mvp
from tkinter import filedialog

class InvoicesView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        lbl_title = ttk.Label(self, text="Faturas Registadas", font=("Segoe UI", 16, "bold"), foreground="#007ACC")
        lbl_title.pack(anchor=tk.W, pady=(0, 15))
        
        # Frame da Tabela
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        columns = ("id", "data", "fornecedor", "categoria", "total", "estado")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("data", text="Data")
        self.tree.heading("fornecedor", text="Fornecedor")
        self.tree.heading("categoria", text="Categoria")
        self.tree.heading("total", text="Total (€)")
        self.tree.heading("estado", text="Estado")
        
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("data", width=100, anchor=tk.CENTER)
        self.tree.column("fornecedor", width=150)
        self.tree.column("categoria", width=120)
        self.tree.column("total", width=80, anchor=tk.E)
        self.tree.column("estado", width=100, anchor=tk.CENTER)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Botões de Ação
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=15)
        
        btn_refresh = ttk.Button(btn_frame, text="🔄 Atualizar Tabela", command=self.load_data)
        btn_refresh.pack(side=tk.LEFT, padx=5, ipady=4)
        
        btn_view_details = ttk.Button(btn_frame, text="👁️ Ver Detalhes", command=self.view_details)
        btn_view_details.pack(side=tk.LEFT, padx=5, ipady=4)
        
        btn_edit = ttk.Button(btn_frame, text="✏️ Editar Fatura", command=self.edit_invoice)
        btn_edit.pack(side=tk.LEFT, padx=5, ipady=4)
        
        btn_delete = ttk.Button(btn_frame, text="🗑️ Eliminar Fatura", command=self.delete_invoice)
        btn_delete.pack(side=tk.LEFT, padx=5, ipady=4)
        
        btn_gerar = ttk.Button(btn_frame, text="G Lançamentos Selecionados", command=self.gerar_selecionados)
        btn_gerar.pack(side=tk.RIGHT, padx=5, ipady=4)
        
        btn_export = ttk.Button(btn_frame, text="Exportar SAFT", command=self.export_saft_action, style="Accent.TButton")
        btn_export.pack(side=tk.RIGHT, padx=5, ipady=4)
        
    def load_data(self):
        # Limpar tabela
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        db = get_session()
        try:
            # JOIN Fatura com Fornecedor e Categoria (Left outer joins)
            faturas = db.query(Fatura, Fornecedor, Categoria).\
                outerjoin(Fornecedor, Fatura.fornecedor_id == Fornecedor.id).\
                outerjoin(Categoria, Fatura.categoria_id == Categoria.id).\
                order_by(Fatura.id.desc()).all()
                
            for ft, fn, cat in faturas:
                nome_fn = fn.nome if fn else "Desconhecido"
                nome_cat = cat.nome if cat else "Não Classificado"
                total_str = f"{ft.total:.2f}" if ft.total else "0.00"
                data_str = ft.data if ft.data else "Sem Data"
                
                self.tree.insert("", tk.END, values=(ft.id, data_str, nome_fn, nome_cat, total_str, ft.estado))
        except Exception as e:
             messagebox.showerror("Erro de BD", f"Erro a carregar faturas: {str(e)}")
        finally:
            db.close()
            
    def gerar_selecionados(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Aviso", "Selecione pelo menos uma fatura na tabela.")
            return
            
        success_count = 0
        for item in selected_items:
            # Pega o ID da fatura (que é o primeiro valor da linha)
            fatura_id = self.tree.item(item, "values")[0]
            sucesso, msg = gerar_lancamento_automatico(fatura_id)
            if sucesso:
                success_count += 1
                
        if success_count > 0:
            messagebox.showinfo("Concluído", f"{success_count} lançamentos gerados com sucesso!")
            self.load_data()
        else:
            messagebox.showinfo("Aviso", "Nenhum novo lançamento gerado (já estavam contabilizadas ou erro).")

    def export_saft_action(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xml",
            filetypes=[("Ficheiro XML", "*.xml")],
            title="Guardar SAFT Simplificado"
        )
        if filepath:
            sucesso, msg = export_saft_mvp(filepath)
            if sucesso:
                messagebox.showinfo("Exportação", msg)
            else:
                messagebox.showerror("Erro", msg)

    def view_details(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Aviso", "Selecione uma fatura na tabela primeiro.")
            return
            
        fatura_id = self.tree.item(selected_items[0], "values")[0]
        
        # Pop-up para mostrar os artigos
        top = tk.Toplevel(self)
        top.title(f"Artigos da Fatura #{fatura_id}")
        top.geometry("600x400")
        top.transient(self.winfo_toplevel()) # Fica por cima da janela original
        top.grab_set() # Foco na nova janela
        
        lbl = ttk.Label(top, text=f"Detalhe de Artigos Extraídos via OCR", font=("Helvetica", 12, "bold"))
        lbl.pack(pady=10)
        
        # Tabela de artigos
        colunas = ("descricao", "valor")
        art_tree = ttk.Treeview(top, columns=colunas, show="headings", height=12)
        art_tree.heading("descricao", text="Descrição do Artigo")
        art_tree.heading("valor", text="Valor (€)")
        art_tree.column("descricao", width=400)
        art_tree.column("valor", width=100, anchor=tk.E)
        art_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        db = get_session()
        try:
            artigos = db.query(ArtigoFatura).filter(ArtigoFatura.fatura_id == fatura_id).all()
            if not artigos:
                art_tree.insert("", tk.END, values=("(A fatura não tem artigos especificados ou o OCR não captou formato válido)", "---"))
            else:
                for art in artigos:
                    art_tree.insert("", tk.END, values=(art.descricao, f"{art.valor:.2f}"))
        except Exception as e:
            messagebox.showerror("Erro de BD", f"Erro a carregar artigos: {str(e)}")
        finally:
            db.close()
            
        btn_fechar = ttk.Button(top, text="Fechar", command=top.destroy)
        btn_fechar.pack(pady=10)

    def edit_invoice(self, fatura_id=None):
        if fatura_id is None:
            selected_items = self.tree.selection()
            if not selected_items:
                messagebox.showwarning("Aviso", "Selecione uma fatura na tabela primeiro.")
                return
            fatura_id = self.tree.item(selected_items[0], "values")[0]
        
        db = get_session()
        # Query completa
        fatura = db.query(Fatura).filter(Fatura.id == fatura_id).first()
        if not fatura:
            db.close()
            return
            
        # Obter Fornecedor e Categoria
        fornecedor = db.query(Fornecedor).filter(Fornecedor.id == fatura.fornecedor_id).first()
        categoria = db.query(Categoria).filter(Categoria.id == fatura.categoria_id).first()
        artigos = db.query(ArtigoFatura).filter(ArtigoFatura.fatura_id == fatura_id).all()
            
        # Pop-up de Edição (Maior para conter tabela)
        top = tk.Toplevel(self)
        top.title(f"Editar Fatura #{fatura.id}")
        top.geometry("700x600")
        top.transient(self.winfo_toplevel())
        top.grab_set()
        
        # --- HEADER / METADADOS ---
        frm_meta = ttk.LabelFrame(top, text="Cabeçalho da Fatura")
        frm_meta.pack(fill=tk.X, padx=10, pady=5)
        
        # Fornecedor
        frm_fn = ttk.Frame(frm_meta)
        frm_fn.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(frm_fn, text="Fornecedor:", width=15).pack(side=tk.LEFT)
        ent_fn = ttk.Entry(frm_fn)
        ent_fn.insert(0, fornecedor.nome if fornecedor else "Desconhecido")
        ent_fn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Categoria
        frm_cat = ttk.Frame(frm_meta)
        frm_cat.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(frm_cat, text="Categoria:", width=15).pack(side=tk.LEFT)
        todas_cats = [c.nome for c in db.query(Categoria).all()]
        if not todas_cats: todas_cats = ["Outros"]
        cb_cat = ttk.Combobox(frm_cat, values=todas_cats)
        cb_cat.set(categoria.nome if categoria else "Outros")
        cb_cat.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Data
        frm_data = ttk.Frame(frm_meta)
        frm_data.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(frm_data, text="Data:", width=15).pack(side=tk.LEFT)
        ent_data = ttk.Entry(frm_data)
        ent_data.insert(0, fatura.data if fatura.data else "")
        ent_data.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Total
        frm_total = ttk.Frame(frm_meta)
        frm_total.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(frm_total, text="Total Geral (€):", width=15).pack(side=tk.LEFT)
        ent_total = ttk.Entry(frm_total)
        ent_total.insert(0, str(fatura.total) if fatura.total else "0.00")
        ent_total.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # --- ARTIGOS / LINHAS ---
        frm_arts = ttk.LabelFrame(top, text="Linhas / Artigos")
        frm_arts.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scroll & Canvas Setup for dynamic entries
        canvas = tk.Canvas(frm_arts)
        scrollbar = ttk.Scrollbar(frm_arts, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Títulos
        ttk.Label(scrollable_frame, text="Descrição do Artigo", font=("Helvetica", 9, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(scrollable_frame, text="Valor (€)", font=("Helvetica", 9, "bold")).grid(row=0, column=1, padx=5, pady=5, sticky=tk.E)
        
        artigo_entries = []
        
        def add_artigo_row(desc="", val="0.00", db_id=None):
            row_idx = len(artigo_entries) + 1
            e_desc = ttk.Entry(scrollable_frame, width=50)
            e_desc.insert(0, desc)
            e_desc.grid(row=row_idx, column=0, padx=5, pady=2, sticky=tk.W)
            
            e_val = ttk.Entry(scrollable_frame, width=15)
            e_val.insert(0, str(val))
            e_val.grid(row=row_idx, column=1, padx=5, pady=2, sticky=tk.E)
            
            artigo_entries.append({
                "id": db_id,
                "desc_entry": e_desc,
                "val_entry": e_val
            })
            
        # Popular linhas existentes
        if artigos:
            for art in artigos:
                add_artigo_row(art.descricao, art.valor, art.id)
        else:
            add_artigo_row() # Pelo menos uma linha vazia
            
        btn_add = ttk.Button(frm_arts, text="+ Nova Linha", command=lambda: add_artigo_row())
        btn_add.pack(anchor=tk.W, padx=5, pady=5)
        
        
        # --- AÇÕES ---
        def save_changes():
            try:
                # 1. Update Cabeçalho
                nova_data = ent_data.get().strip()
                novo_total = float(ent_total.get().strip().replace(',', '.'))
                
                fatura.data = nova_data
                fatura.total = novo_total
                
                # Update/Create Fornecedor
                novo_fornecedor_nome = ent_fn.get().strip()
                if fornecedor:
                    fornecedor.nome = novo_fornecedor_nome
                else:
                    novo_fn = Fornecedor(nome=novo_fornecedor_nome, nif="")
                    db.add(novo_fn)
                    db.flush()
                    fatura.fornecedor_id = novo_fn.id
                    
                # Update/Create Categoria
                nova_cat_nome = cb_cat.get().strip()
                if categoria.nome != nova_cat_nome:
                    cat_existente = db.query(Categoria).filter(Categoria.nome == nova_cat_nome).first()
                    if cat_existente:
                        fatura.categoria_id = cat_existente.id
                    else:
                        nova_cat = Categoria(nome=nova_cat_nome, conta_debito_codigo="62")
                        db.add(nova_cat)
                        db.flush()
                        fatura.categoria_id = nova_cat.id
                
                # 2. Update Artigos
                # Para simplificar a sincronização UI->BD sem tracking complexo:
                # Apagamos os velhos e inserimos os novos validados que não estejam em branco
                db.query(ArtigoFatura).filter(ArtigoFatura.fatura_id == fatura.id).delete()
                
                for row in artigo_entries:
                    d = row["desc_entry"].get().strip()
                    v_str = row["val_entry"].get().strip().replace(',', '.')
                    
                    if d: # Só salva se a linha tiver descrição
                        v = float(v_str) if v_str else 0.0
                        novo_art = ArtigoFatura(fatura_id=fatura.id, descricao=d, valor=v)
                        db.add(novo_art)
                
                # 3. Commit Final
                db.commit()
                messagebox.showinfo("Sucesso", "Fatura e Artigos atualizados com sucesso!")
                top.destroy()
                self.load_data() 
                
            except ValueError:
                messagebox.showerror("Erro de Validação", "Um ou mais valores numéricos (Preços) têm um formato inválido.")
            except Exception as e:
                db.rollback()
                messagebox.showerror("Erro de Gravação", f"Ocorreu um erro: {str(e)}")
                
        # Botões Rodapé
        btn_frm = ttk.Frame(top)
        btn_frm.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frm, text="Gravar Alterações", command=save_changes, style="Accent.TButton").pack(side=tk.RIGHT, padx=20)
        ttk.Button(btn_frm, text="Cancelar", command=lambda: [top.destroy(), db.close()]).pack(side=tk.RIGHT)

    def delete_invoice(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Aviso", "Selecione uma fatura na tabela primeiro.")
            return
            
        fatura_id = self.tree.item(selected_items[0], "values")[0]
        
        if messagebox.askyesno("Confirmar", f"Tem a certeza que deseja eliminar a fatura #{fatura_id} do sistema?\n\nIsto irá eliminar também os lançamentos contabilísticos e os artigos associados. O ficheiro original continuará na pasta processada."):
            db = get_session()
            try:
                # 1. Eliminar Lançamentos associados
                db.query(Lancamento).filter(Lancamento.fatura_id == fatura_id).delete()
                
                # 2. Eliminar Artigos associados
                db.query(ArtigoFatura).filter(ArtigoFatura.fatura_id == fatura_id).delete()
                
                # 3. Eliminar a Fatura
                db.query(Fatura).filter(Fatura.id == fatura_id).delete()
                
                db.commit()
                messagebox.showinfo("Sucesso", "Fatura eliminada com sucesso.")
                self.load_data()
            except Exception as e:
                db.rollback()
                messagebox.showerror("Erro de BD", f"Erro a eliminar fatura: {str(e)}")
            finally:
                db.close()

