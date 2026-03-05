import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from core.database import get_session
from core.models import Fornecedor, Fatura, Categoria
from sqlalchemy import func

class CRMView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.canvas_widget = None
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        lbl_title = ttk.Label(self, text="🤝 Gestão de Entidades (CRM)", font=("Segoe UI", 16, "bold"), foreground="#007ACC")
        lbl_title.pack(anchor=tk.W, pady=(0, 15))
        
        # Filtros / Ações
        frm_actions = ttk.Frame(self)
        frm_actions.pack(fill=tk.X, pady=(0, 10))
        
        btn_refresh = ttk.Button(frm_actions, text="⟲ Atualizar Dados", command=self.load_data, style="Accent.TButton")
        btn_refresh.pack(side=tk.LEFT)
        
        self.lbl_kpi_fornecedores = ttk.Label(frm_actions, text="Fornecedores Registados: --", font=("Segoe UI", 11, "bold"))
        self.lbl_kpi_fornecedores.pack(side=tk.RIGHT, padx=20)
        
        # Split Container: Tabela à Esquerda, Gráficos à Direita
        frm_split = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        frm_split.pack(fill=tk.BOTH, expand=True)
        
        # Tabela Fornecedores
        frm_table = ttk.LabelFrame(frm_split, text="Diretório de Fornecedores", padding=10)
        frm_split.add(frm_table, weight=1)
        
        columns = ("nome", "nif", "faturas", "total_gasto")
        self.tree = ttk.Treeview(frm_table, columns=columns, show="headings", height=15)
        self.tree.heading("nome", text="Nome Entidade")
        self.tree.heading("nif", text="NIF")
        self.tree.heading("faturas", text="Nº Faturas")
        self.tree.heading("total_gasto", text="Total Gasto (€)")
        
        self.tree.column("nome", width=200)
        self.tree.column("nif", width=100)
        self.tree.column("faturas", width=80, anchor=tk.CENTER)
        self.tree.column("total_gasto", width=100, anchor=tk.E)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Area Gráfica
        self.frm_charts = ttk.LabelFrame(frm_split, text="Análise (Top Fornecedores Historicamente)", padding=10)
        frm_split.add(self.frm_charts, weight=1)
        
    def load_data(self):
        db = get_session()
        try:
            # Query the required info: Supplier info + aggregate invoice count and total sum
            dados = db.query(
                Fornecedor.nome,
                Fornecedor.nif,
                func.count(Fatura.id).label("num_fats"),
                func.sum(Fatura.total).label("total")
            ).outerjoin(Fatura, Fornecedor.id == Fatura.fornecedor_id)\
             .group_by(Fornecedor.id)\
             .order_by(func.sum(Fatura.total).desc())\
             .all()
            
            # Limpar tabela
            for row in self.tree.get_children():
                self.tree.delete(row)
                
            self.lbl_kpi_fornecedores.config(text=f"Fornecedores Registados: {len(dados)}")
            
            df_data = []
            
            for f_nome, f_nif, f_count, f_total in dados:
                total_val = f_total if f_total else 0.0
                nif_val = f_nif if f_nif else "N/A"
                nome_val = f_nome if f_nome else "Desconhecido"
                
                self.tree.insert("", tk.END, values=(
                    nome_val,
                    nif_val,
                    f_count,
                    f"{total_val:.2f} €"
                ))
                
                # Exclude internal null/zero suppliers for chart accuracy
                if total_val > 0.1:
                    df_data.append({"Fornecedor": nome_val, "Gasto": total_val})
                
            # Render Charts
            if hasattr(self, 'canvas_widget') and self.canvas_widget:
                self.canvas_widget.get_tk_widget().destroy()
                self.canvas_widget = None
                
            if len(df_data) > 0:
                df = pd.DataFrame(df_data).head(5) # Top 5 only
                
                fig = plt.Figure(figsize=(5, 4), dpi=100)
                ax = fig.add_subplot(111)
                
                bars = ax.barh(df['Fornecedor'], df['Gasto'], color='#007ACC')
                ax.set_title("Maior Volume de Faturação (€)")
                ax.invert_yaxis()  # Labels read top-to-bottom
                ax.set_xlabel("Valor Total")
                
                # Adicionar valores na ponta das barras
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width, bar.get_y() + bar.get_height()/2, f' {width:.2f}€', ha='left', va='center', fontsize=9)
                    
                fig.tight_layout()
                
                self.canvas_widget = FigureCanvasTkAgg(fig, master=self.frm_charts)
                self.canvas_widget.draw()
                self.canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            else:
                ttk.Label(self.frm_charts, text="Sem dados suficientes.").pack(pady=20)
                
        except Exception as e:
            messagebox.showerror("Erro de BD", str(e))
        finally:
            db.close()
