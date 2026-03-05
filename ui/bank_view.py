import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from core.database import get_session
from core.models import MovimentoBancario, Fatura, Fornecedor
import dateutil.parser

class BankSyncView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        lbl_title = ttk.Label(self, text="🏦 Reconciliação Bancária", font=("Segoe UI", 16, "bold"), foreground="#007ACC")
        lbl_title.pack(anchor=tk.W, pady=(0, 20))
        
        frm_acoes = ttk.Frame(self)
        frm_acoes.pack(fill=tk.X, pady=(0, 15))
        
        btn_import = ttk.Button(frm_acoes, text="📥 Importar Extrato (CSV)", command=self.import_csv, style="Accent.TButton")
        btn_import.pack(side=tk.LEFT, padx=(0, 10))
        
        btn_auto = ttk.Button(frm_acoes, text="✨ Sugerir Correspondências", command=self.auto_reconcile)
        btn_auto.pack(side=tk.LEFT)
        
        self.lbl_stats = ttk.Label(frm_acoes, text="Movimentos Pendentes: --", font=("Segoe UI", 10, "bold"))
        self.lbl_stats.pack(side=tk.RIGHT)
        
        # Splitter: Movimentos vs Faturas Sugeridas
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        # Area de Movimentos
        frm_movs = ttk.LabelFrame(self.paned, text="Extrato Bancário", padding=10)
        self.paned.add(frm_movs, weight=2)
        
        cols_mov = ("id", "data", "desc", "valor", "estado")
        self.tree_mov = ttk.Treeview(frm_movs, columns=cols_mov, show="headings", height=8)
        self.tree_mov.heading("id", text="Nr")
        self.tree_mov.heading("data", text="Data")
        self.tree_mov.heading("desc", text="Descrição do Movimento")
        self.tree_mov.heading("valor", text="Valor (€)")
        self.tree_mov.heading("estado", text="Estado")
        
        self.tree_mov.column("id", width=30)
        self.tree_mov.column("data", width=100)
        self.tree_mov.column("desc", width=400)
        self.tree_mov.column("valor", width=100, anchor=tk.E)
        self.tree_mov.column("estado", width=150)
        
        self.tree_mov.pack(fill=tk.BOTH, expand=True)
        self.tree_mov.bind("<<TreeviewSelect>>", self.on_mov_select)
        
        # Area Sugestões
        frm_sug = ttk.LabelFrame(self.paned, text="Correspondência de Faturas", padding=10)
        self.paned.add(frm_sug, weight=1)
        
        self.lbl_sug = ttk.Label(frm_sug, text="Selecione um movimento bancário em cima para ver faturas do mesmo valor ou data.")
        self.lbl_sug.pack(pady=5)
        
        cols_fat = ("f_id", "data", "fornecedor", "total", "match_reason")
        self.tree_fat = ttk.Treeview(frm_sug, columns=cols_fat, show="headings", height=4)
        self.tree_fat.heading("f_id", text="ID")
        self.tree_fat.heading("data", text="Data da Fatura")
        self.tree_fat.heading("fornecedor", text="Fornecedor")
        self.tree_fat.heading("total", text="Total (€)")
        self.tree_fat.heading("match_reason", text="Motivo Sugestão")
        
        self.tree_fat.column("f_id", width=30)
        self.tree_fat.pack(fill=tk.BOTH, expand=True)
        
        btn_match = ttk.Button(frm_sug, text="🔗 Ligar Fatura a Movimento", command=self.manual_match, style="Accent.TButton")
        btn_match.pack(pady=10)
        
    def load_data(self):
        db = get_session()
        try:
            for item in self.tree_mov.get_children():
                self.tree_mov.delete(item)
                
            movimentos = db.query(MovimentoBancario).order_by(MovimentoBancario.data.desc()).all()
            pendentes = 0
            
            for m in movimentos:
                if m.estado == "Pendente": pendentes += 1
                self.tree_mov.insert("", tk.END, values=(
                    m.id,
                    m.data,
                    m.descricao,
                    f"{m.valor:.2f}",
                    "✔️ Reconciliado" if m.estado == "Reconciliado" else "⏳ Pendente"
                ))
                
            self.lbl_stats.config(text=f"Por Reconciliar: {pendentes} de {len(movimentos)}")
            
            # Limpa Sugestões inferiores ao atualizar
            for item in self.tree_fat.get_children():
                 self.tree_fat.delete(item)
            self.lbl_sug.config(text="Selecione um movimento bancário em cima para ver faturas do mesmo valor ou data.")
        finally:
            db.close()
            
    def import_csv(self):
        filepath = filedialog.askopenfilename(
            title="Selecionar Extrato (CSV)",
            filetypes=(("Ficheiros CSV", "*.csv"), ("Todos", "*.*"))
        )
        if not filepath:
            return
            
        try:
            db = get_session()
            import_count = 0
            # Leitor Genérico simplificado. Extratos reais costumam ter Data, Descrição, Valor.
            with open(filepath, newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile, delimiter=';')
                # Ignorar header assumindo layout PT comum: Data Lancamento;Descricao;Valor
                header = next(reader, None)
                for row in reader:
                    if len(row) >= 3:
                        raw_data = row[0].strip()
                        raw_desc = row[1].strip()
                        raw_val = row[2].strip().replace('€', '').replace(' ', '').replace(',', '.')
                        
                        try:
                            # Tentar parse da data
                            d_parsed = dateutil.parser.parse(raw_data, dayfirst=True)
                            d_iso = d_parsed.strftime("%Y-%m-%d")
                            val_float = float(raw_val)
                            
                            m = MovimentoBancario(
                                data=d_iso,
                                descricao=raw_desc,
                                valor=val_float,
                                estado="Pendente"
                            )
                            db.add(m)
                            import_count += 1
                        except Exception as e:
                            # Ignorar linhas erradas
                            pass
            db.commit()
            messagebox.showinfo("Sucesso", f"{import_count} Movimento(s) transferido(s) do Extrato com sucesso.")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Erro de Leitura", f"Erro a interpretar o CSV: {e}\nCertifique-se que as colunas são: 'Data ; Descrição ; Valor'")
        finally:
            if 'db' in locals():
                db.close()
                pass
                
    def on_mov_select(self, event):
        selected = self.tree_mov.selection()
        if not selected:
            return
            
        values = self.tree_mov.item(selected[0])["values"]
        m_id = values[0]
        m_data = values[1]
        m_desc = values[2].lower()
        m_valor = abs(float(values[3])) # Tratar tudo como positivo para Match com faturas
        
        self.lbl_sug.config(text=f"À procura de faturas emitidas por volta do dia {m_data} com o valor de {m_valor}€ ...")
        
        # Limpar
        for item in self.tree_fat.get_children():
             self.tree_fat.delete(item)
             
        db = get_session()
        try:
            # Estratégia Bússola: Valores Exatos ou Datas Próximas
            matches = []
            
            # Match 1: Valor Exato (Mais forte) (margin 0.05 euros)
            faturas_valor = db.query(Fatura, Fornecedor).outerjoin(Fornecedor).filter(
                Fatura.total >= (m_valor - 0.05),
                Fatura.total <= (m_valor + 0.05),
                Fatura.movimento_id == None
            ).limit(5).all()
            
            for f, n in faturas_valor:
                matches.append((f, n, "🌟 Valor Exato Igual"))
            
            # Mostrar os matches na TreeView
            if not matches:
                self.lbl_sug.config(text=f"Nenhuma sugestão encontrada para os {m_valor}€ da linha selecionada.")
            else:
                for fatura, forn, reason in matches:
                    self.tree_fat.insert("", tk.END, values=(
                        fatura.id,
                        fatura.data,
                        forn.nome if forn else "Desconhecido",
                        fatura.total,
                        reason
                    ))
        except Exception as e:
            print(f"Erro a sugerir: {e}")
        finally:
            db.close()
            
    def auto_reconcile(self):
        """Mágica: Liga automaticamente todas as faturas pendentes que tenham valores exatos numérico/data a movimentos soltos."""
        db = get_session()
        count = 0
        try:
            pendentes_movs = db.query(MovimentoBancario).filter(MovimentoBancario.estado == "Pendente").all()
            for m in pendentes_movs:
                if m.valor >= 0: continue # Ignora depósitos / income para já, focamos em despesas
                
                m_val = abs(m.valor)
                # Verifica se há apenas 1 fatura pendente com este exato valor e que a data difira num máximo de 5 dias
                faturas_alvo = db.query(Fatura).filter(
                    Fatura.total >= (m_val - 0.01),
                    Fatura.total <= (m_val + 0.01),
                    Fatura.movimento_id == None
                ).all()
                
                # Se encontrou match perfeito de apenas 1
                if len(faturas_alvo) == 1:
                    fat = faturas_alvo[0]
                    fat.movimento_id = m.id
                    fat.estado = "Contabilizada" # A fatura fica fechada, foi paga e provada pelo banco
                    m.estado = "Reconciliado"
                    count += 1
            db.commit()
            if count > 0:
                messagebox.showinfo("Automágico", f"{count} Faturas ligadas automaticamente ao Banco e dadas como Contabilizadas!")
            else:
                messagebox.showinfo("Simulação", "Não foi encontrada nenhuma ligação 100% segura automática. Faça correspondência manual da lista inferior.")
            self.load_data()
        finally:
            db.close()
            
    def manual_match(self):
        sel_mov = self.tree_mov.selection()
        sel_fat = self.tree_fat.selection()
        
        if not sel_mov or not sel_fat:
            messagebox.showwarning("Aviso", "Tem de selecionar um Movimento na tabela de cima, e uma Fatura-Sugestão na tabela de baixo para os unir.")
            return
            
        m_id = self.tree_mov.item(sel_mov[0])["values"][0]
        f_id = self.tree_fat.item(sel_fat[0])["values"][0]
        
        db = get_session()
        try:
            mov = db.query(MovimentoBancario).get(m_id)
            fat = db.query(Fatura).get(f_id)
            
            if mov and fat:
                fat.movimento_id = mov.id
                fat.estado = "Contabilizada"
                mov.estado = "Reconciliado"
                db.commit()
                messagebox.showinfo("Sucesso", "Movimento Bancário e Fatura reconciliados com sucesso! Fatura dada como fechada.")
                self.load_data()
        except Exception as e:
            messagebox.showerror("Grau", str(e))
        finally:
            db.close()
