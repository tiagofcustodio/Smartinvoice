import tkinter as tk
from tkinter import ttk, messagebox
from core.database import get_session
from core.models import Fatura, ArtigoFatura, DefinicoesPerfil
import datetime

class IvaView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.setup_ui()
        self.load_profile_config()
        
    def setup_ui(self):
        lbl_title = ttk.Label(self, text="Declaração de IVA", font=("Segoe UI", 16, "bold"), foreground="#007ACC")
        lbl_title.pack(anchor=tk.W, pady=(0, 15))
        
        # Profile Info
        self.lbl_regime = ttk.Label(self, text="Regime de IVA: A carregar...", font=("Segoe UI", 10, "italic"))
        self.lbl_regime.pack(anchor=tk.W, pady=(0, 15))
        
        # Filtro de Trimestre
        frm_filter = ttk.LabelFrame(self, text="Período Fiscais")
        frm_filter.pack(fill=tk.X, pady=5, ipady=5, ipadx=5)
        
        ttk.Label(frm_filter, text="Trimestre:").pack(side=tk.LEFT, padx=(5, 10))
        
        self.combo_trimestre = ttk.Combobox(frm_filter, state="readonly", width=30)
        self.combo_trimestre['values'] = [
            "1º Trimestre (Jan - Mar)",
            "2º Trimestre (Abr - Jun)",
            "3º Trimestre (Jul - Set)",
            "4º Trimestre (Out - Dez)"
        ]
        
        # Set default to current quarter
        current_month = datetime.datetime.now().month
        current_quarter = (current_month - 1) // 3
        self.combo_trimestre.current(current_quarter)
        self.combo_trimestre.pack(side=tk.LEFT)
        
        # Vendas / Receitas Manuais
        frm_rendimentos = ttk.LabelFrame(self, text="1. As Vossas Vendas / Rendimentos (Lançamento Manual)")
        frm_rendimentos.pack(fill=tk.X, pady=10, ipady=10, ipadx=10)
        
        ttk.Label(frm_rendimentos, text="Total Faturado s/ IVA (€):").grid(row=0, column=0, pady=5, sticky=tk.E)
        self.ent_faturado = ttk.Entry(frm_rendimentos, width=15)
        self.ent_faturado.insert(0, "0.00")
        self.ent_faturado.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        
        ttk.Label(frm_rendimentos, text="IVA Liquidado a Clientes (€):").grid(row=1, column=0, pady=5, sticky=tk.E)
        self.ent_iva_liquidado = ttk.Entry(frm_rendimentos, width=15)
        self.ent_iva_liquidado.insert(0, "0.00")
        self.ent_iva_liquidado.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Botão Calcular
        btn_calc = ttk.Button(self, text="🧮 Calcular Apuramento de IVA", command=self.calculate_iva, style="Accent.TButton")
        btn_calc.pack(pady=15, ipady=5)
        
        # Resultados
        self.frm_resultados = ttk.LabelFrame(self, text="2. Apuramento do Estado")
        self.frm_resultados.pack(fill=tk.BOTH, expand=True, pady=5, ipadx=10, ipady=10)
        
        # Metrics setup
        self.lbl_despesas_elegiveis = ttk.Label(self.frm_resultados, text="Total Despesas Elegíveis: 0.00 €", font=("Segoe UI", 12))
        self.lbl_despesas_elegiveis.pack(anchor=tk.W, pady=5)
        
        self.lbl_iva_dedutivel = ttk.Label(self.frm_resultados, text="Total IVA Dedutível: 0.00 €", font=("Segoe UI", 12))
        self.lbl_iva_dedutivel.pack(anchor=tk.W, pady=5)
        
        ttk.Separator(self.frm_resultados, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        self.lbl_resultado_final = ttk.Label(self.frm_resultados, text="IVA a Entregar / Crédito: --", font=("Segoe UI", 18, "bold"))
        self.lbl_resultado_final.pack(anchor=tk.CENTER, pady=10)
        
        # Export Button
        btn_export = ttk.Button(self.frm_resultados, text="📄 Gerar Resumo para Declaração", command=self.generate_report)
        btn_export.pack(side=tk.BOTTOM, anchor=tk.E, pady=(10, 0))

    def load_profile_config(self):
        db = get_session()
        try:
            perfil = db.query(DefinicoesPerfil).first()
            if perfil:
                self.lbl_regime.config(text=f"📌 Regime de IVA Atual: {perfil.regime_iva}")
        finally:
            db.close()
            
    def _get_quarter_months(self, quarter_str):
        if "1º" in quarter_str: return ['01', '02', '03']
        if "2º" in quarter_str: return ['04', '05', '06']
        if "3º" in quarter_str: return ['07', '08', '09']
        if "4º" in quarter_str: return ['10', '11', '12']
        return []

    def calculate_iva(self):
        db = get_session()
        try:
            # Lidar com os inputs manuais
            try:
                liquidado = float(self.ent_iva_liquidado.get().replace(',', '.'))
            except ValueError:
                liquidado = 0.0
                
            trimestre = self.combo_trimestre.get()
            meses_alvo = self._get_quarter_months(trimestre)
            ano_atual = datetime.datetime.now().year # Assumindo cálculos do ano corrente local
            
            # Queremos obter as faturas do tipo "Despesas da atividade"
            iva_dedutivel_somatorio = 0.0
            total_despesas_somatorio = 0.0
            
            faturas = db.query(Fatura).filter(
                Fatura.tipo_despesa == "Despesas da atividade"
            ).all()
            
            # Filtro Python por mês
            faturas_trimestre = []
            for f in faturas:
                if not f.data or len(f.data) < 7:
                    continue
                ano_f, mes_f = f.data[:4], f.data[5:7]
                if int(ano_f) == ano_atual and mes_f in meses_alvo:
                    faturas_trimestre.append(f)
                    
            # Iterar nas faturas para cruzar IVA por artigo com o grau de dedutibilidade da Fatura
            for f in faturas_trimestre:
                artigos = db.query(ArtigoFatura).filter(ArtigoFatura.fatura_id == f.id).all()
                iva_fatura_isolado = 0.0
                
                # Para cada artigo, sabemos o valor final (já com IVA) e a taxa de IVA.
                # Valor sem IVA = Valor Final / (1 + Taxa/100)
                # IVA do artigo = Valor Final - Valor sem IVA
                for art in artigos:
                    taxa = art.taxa_iva if art.taxa_iva else 0.0
                    if taxa > 0:
                        valor_sem_iva = art.valor / (1 + (taxa / 100))
                        valor_iva = art.valor - valor_sem_iva
                        iva_fatura_isolado += valor_iva
                
                grau = (f.grau_dedutibilidade / 100.0) if f.grau_dedutibilidade else 1.0
                iva_deduzido_esta_fatura = iva_fatura_isolado * grau
                
                iva_dedutivel_somatorio += iva_deduzido_esta_fatura
                total_despesas_somatorio += (f.total * grau) if f.total else 0.0
                
            # Atualizar Labels
            self.lbl_despesas_elegiveis.config(text=f"Total Despesas Elegíveis: {total_despesas_somatorio:.2f} €")
            self.lbl_iva_dedutivel.config(text=f"Total IVA Dedutível: {iva_dedutivel_somatorio:.2f} €")
            
            # Apuramento: Liquidado - Dedutível
            resultado = liquidado - iva_dedutivel_somatorio
            
            if resultado > 0:
                self.lbl_resultado_final.config(text=f"IVA a Entregar ao Estado: {resultado:.2f} €", foreground="red")
            elif resultado < 0:
                self.lbl_resultado_final.config(text=f"Crédito de IVA: {abs(resultado):.2f} €", foreground="green")
            else:
                self.lbl_resultado_final.config(text="Sem Apuramento a Pagar: 0.00 €", foreground="black")

        except Exception as e:
            messagebox.showerror("Erro de Cálculo", f"Ocorreu um erro ao calcular o Apuramento de IVA:\n{str(e)}")
        finally:
            db.close()
            
    def generate_report(self):
        from tkinter import filedialog
        import os
        
        resultado = self.lbl_resultado_final.cget("text")
        if resultado == "IVA a Entregar / Crédito: --":
            messagebox.showwarning("Sem Cálculos", "Por favor, clique em 'Calcular Apuramento de IVA' primeiro.")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Documento de Texto", "*.txt")],
            title="Exportar Resumo de IVA"
        )
        if not filepath: return
        
        try:
            with open(filepath, "w", encoding="utf-8") as file:
                file.write("="*40 + "\n")
                file.write(f"RESUMO DE APURAMENTO DE IVA\n")
                file.write(f"Período: {self.combo_trimestre.get()}\n")
                file.write(self.lbl_regime.cget("text") + "\n")
                file.write("="*40 + "\n\n")
                
                file.write(f"1) Total Faturado s/ IVA: {self.ent_faturado.get()} €\n")
                file.write(f"2) IVA Liquidado (Recebido de Clientes): {self.ent_iva_liquidado.get()} €\n\n")
                
                file.write(f"3) {self.lbl_despesas_elegiveis.cget('text')}\n")
                file.write(f"4) {self.lbl_iva_dedutivel.cget('text')}\n\n")
                
                file.write("="*40 + "\n")
                file.write(f"RESULTADO FINAL: {resultado}\n")
                file.write("="*40 + "\n\n")
                file.write("Nota: Este resumo é gerado automaticamente pelo SmartInvoice baseando-se nos registos inseridos e regras de cruzamento com o perfil. Por favor, confirme sempre com o seu contabilista certificado.")
                
            messagebox.showinfo("Exportado", f"O resumo foi guardado em:\n{filepath}\n\nPode enviá-lo por e-mail ao seu contabilista.")
        except Exception as e:
            messagebox.showerror("Erro de Exportação", f"Falha ao guardar o ficheiro: {e}")
