import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from core.database import get_session
from core.models import Fatura, Fornecedor, Categoria, ArtigoFatura
from core.exporter import export_monthly_reports
import datetime
import os

class MonthlyView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.setup_ui()
        
    def get_available_months(self):
        db = get_session()
        try:
            # Extrair os meses únicos (YYYY-MM) das faturas registadas
            faturas = db.query(Fatura.data).filter(Fatura.data.isnot(None), Fatura.data != "").all()
            meses = set()
            for (d,) in faturas:
                try:
                    # Assumindo formato YYYY-MM-DD
                    if len(d) >= 7:
                        meses.add(d[:7])
                except:
                    pass
            
            lista_meses = sorted(list(meses), reverse=True)
            return lista_meses if lista_meses else [datetime.datetime.now().strftime("%Y-%m")]
        finally:
            db.close()

    def setup_ui(self):
        lbl_title = ttk.Label(self, text="Resumo Mensal e Estatísticas", font=("Segoe UI", 16, "bold"), foreground="#007ACC")
        lbl_title.pack(anchor=tk.W, pady=(0, 15))
        
        # Filtro de Mês
        frm_filter = ttk.Frame(self)
        frm_filter.pack(fill=tk.X, pady=5)
        
        ttk.Label(frm_filter, text="Selecione o Mês:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.combo_mes = ttk.Combobox(frm_filter, state="readonly", width=15)
        self.combo_mes.pack(side=tk.LEFT)
        self.combo_mes.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        
        btn_refresh = ttk.Button(frm_filter, text="Atualizar Dados", command=self.load_data, style="Accent.TButton")
        btn_refresh.pack(side=tk.LEFT, padx=10, ipady=4)
        
        btn_export = ttk.Button(frm_filter, text="📊 Exportar Excel", command=self.action_export, style="Accent.TButton")
        btn_export.pack(side=tk.RIGHT, padx=10, ipady=4)
        
        # Container de KPIs
        self.frm_kpis = ttk.Frame(self)
        self.frm_kpis.pack(fill=tk.X, pady=10)
        
        # Container para os gráficos
        self.frm_graphs = ttk.Frame(self)
        self.frm_graphs.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Area de Top Artigos
        self.frm_artigos = ttk.LabelFrame(self, text="Artigos Mais Caros Deste Mês")
        self.frm_artigos.pack(fill=tk.X, pady=10)
        
        self.tree_artigos = ttk.Treeview(self.frm_artigos, columns=("desc", "fornecedor", "data", "valor"), show="headings", height=5)
        self.tree_artigos.heading("desc", text="Descrição do Artigo")
        self.tree_artigos.heading("fornecedor", text="Fornecedor")
        self.tree_artigos.heading("data", text="Data")
        self.tree_artigos.heading("valor", text="Valor (€)")
        self.tree_artigos.column("desc", width=300)
        self.tree_artigos.column("valor", width=100, anchor=tk.E)
        self.tree_artigos.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        # Canvas Holder
        self.canvas_widget = None

        self.canvas_widget = None

    def action_export(self):
        mes = self.combo_mes.get()
        if not mes:
            messagebox.showwarning("Aviso", "Selecione um mês primeiro.")
            return
            
        sucesso, msg = export_monthly_reports(mes)
        if sucesso:
            # Perguntar se quer abrir a pasta do report
            if messagebox.askyesno("Exportação Concluída", f"Ficheiro guardado com sucesso em:\n{msg}\n\nDeseja abrir a pasta agora?"):
                os.startfile(os.path.dirname(msg))
        else:
            messagebox.showerror("Erro na exportação", f"Ocorreu um erro a gerar o Excel:\n{msg}")

    def refresh_months_list(self):
        meses = self.get_available_months()
        self.combo_mes['values'] = meses
        if meses:
            if not self.combo_mes.get() in meses:
               self.combo_mes.set(meses[0])

    def load_data(self):
        mes_selecionado = self.combo_mes.get()
        if not mes_selecionado:
            return
            
        db = get_session()
        try:
            # Obter faturas do mês selecionado
            # Sqlite LIKE query (ex: '2023-10%')
            faturas = db.query(Fatura, Fornecedor, Categoria).\
                outerjoin(Fornecedor, Fatura.fornecedor_id == Fornecedor.id).\
                outerjoin(Categoria, Fatura.categoria_id == Categoria.id).\
                filter(Fatura.data.like(f"{mes_selecionado}%")).all()
                
            total_gasto = sum(f.Fatura.total for f in faturas if f.Fatura.total)
            num_faturas = len(faturas)
            
            # Limpar KPIs antigos
            for widget in self.frm_kpis.winfo_children():
                widget.destroy()
                
            # Renderizar KPIs
            lbl_total = ttk.Label(self.frm_kpis, text=f"Total Gasto: {total_gasto:.2f} €", font=("Segoe UI", 14, "bold"), foreground="#007ACC")
            lbl_total.pack(side=tk.LEFT, padx=20)
            
            lbl_qtd = ttk.Label(self.frm_kpis, text=f"Documentos: {num_faturas}", font=("Segoe UI", 12))
            lbl_qtd.pack(side=tk.LEFT, padx=20)
            
            # Se não houver dados, limpa os gráficos
            if hasattr(self, 'canvas_widget') and self.canvas_widget:
                self.canvas_widget.get_tk_widget().destroy()
                self.canvas_widget = None
                
            if num_faturas == 0:
                ttk.Label(self.frm_graphs, text="Não há faturas registadas neste mês.").pack()
                return
                
            # Processar dados com Pandas para os gráficos
            dados = []
            for ft, fn, cat in faturas:
                dados.append({
                    "data": ft.data,
                    "dia": ft.data[-2:] if ft.data and len(ft.data) >= 10 else "01",
                    "total": ft.total if ft.total else 0,
                    "categoria": cat.nome if cat else "Não Classificado",
                    "fornecedor": fn.nome if fn else "Desconhecido"
                })
                
            df = pd.DataFrame(dados)
            
            # Desenhar Gráficos
            fig = plt.Figure(figsize=(10, 4), dpi=100)
            
            # 1. Gráfico de Barras por Categoria (Pie)
            ax1 = fig.add_subplot(121)
            cat_totals = df.groupby('categoria')['total'].sum()
            if not cat_totals.empty and cat_totals.sum() > 0:
                ax1.pie(cat_totals, labels=cat_totals.index, autopct='%1.1f%%', startangle=90)
                ax1.set_title("Gastos por Categoria")
            else:
                 ax1.text(0.5, 0.5, 'Sem dados de categorias', horizontalalignment='center')
                 ax1.axis('off')
            
            # 2. Gráfico por Fornecedor (Top 5)
            ax2 = fig.add_subplot(122)
            fn_totals = df.groupby('fornecedor')['total'].sum().nlargest(5)
            if not fn_totals.empty:
                fn_totals.plot(kind='barh', ax=ax2, color='steelblue')
                ax2.set_xlabel('Total (€)')
                ax2.set_title("Top 5 Fornecedores")
                ax2.invert_yaxis()  # O maior fica em cima
            else:
                 ax2.text(0.5, 0.5, 'Sem dados de fornecedores', horizontalalignment='center')
                 ax2.axis('off')
            
            fig.tight_layout()
            
            # Integrar Matplotlib no Tkinter
            self.canvas_widget = FigureCanvasTkAgg(fig, master=self.frm_graphs)
            self.canvas_widget.draw()
            canvas_tk = self.canvas_widget.get_tk_widget()
            canvas_tk.pack(fill=tk.BOTH, expand=True)
            
            # Carregar Top Artigos (Query complexa via ORM)
            # Vamos buscar todos os artigos das faturas deste mês, ordenados por valor desc
            for item in self.tree_artigos.get_children():
                self.tree_artigos.delete(item)
                
            faturas_ids = [f.Fatura.id for f in faturas]
            if faturas_ids:
                artigos = db.query(ArtigoFatura, Fatura, Fornecedor).\
                    join(Fatura, ArtigoFatura.fatura_id == Fatura.id).\
                    outerjoin(Fornecedor, Fatura.fornecedor_id == Fornecedor.id).\
                    filter(ArtigoFatura.fatura_id.in_(faturas_ids)).\
                    order_by(ArtigoFatura.valor.desc()).limit(10).all()
                    
                for art, fat, fn in artigos:
                    nome_fn = fn.nome if fn else "Desconhecido"
                    val_str = f"{art.valor:.2f}" if art.valor else "0.00"
                    self.tree_artigos.insert("", tk.END, values=(art.descricao, nome_fn, fat.data, val_str))

        except Exception as e:
            messagebox.showerror("Erro Estatísticas", f"Ocorreu um erro a gerar o resumo: {str(e)}")
        finally:
            db.close()
