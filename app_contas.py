import streamlit as st
import pandas as pd
import pdfplumber
import re
import io
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Contas da Congregação - S-26 & S-30", layout="wide", page_icon="📑")

st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #2b5c8f;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .s30-box {
        background-color: #fffef5;
        border: 2px solid #e0c870;
        border-radius: 10px;
        padding: 20px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
</style>
""", unsafe_allow_html=True)

MONTH_ORDER = {
    'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3, 'abril': 4,
    'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8, 'setembro': 9,
    'outubro': 10, 'novembro': 11, 'dezembro': 12
}

def parse_s26_pdf(file_bytes):
    """Extrai informações e transações do PDF S-26 do JW Hub."""
    text_full = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text_full += page.extract_text() + "\n"
    
    # Extrai mês e ano
    header_match = re.search(r'([a-zçA-ZÇ]+)\s+de\s+(20\d\d)', text_full, re.IGNORECASE)
    mes_str = header_match.group(1).lower() if header_match else "indefinido"
    ano_str = header_match.group(2) if header_match else "2026"
    
    # Extrai saldo final disponível
    saldo_disp = 0.0
    saldo_match = re.search(r'SALDO DISPON[ÍI]VEL NO FINAL DO M[ÊE]S.*?([\d\.,]+)', text_full, re.DOTALL | re.IGNORECASE)
    if saldo_match:
        try:
            val_txt = saldo_match.group(1).strip().replace('.', '').replace(',', '.')
            saldo_disp = float(val_txt)
        except:
            saldo_disp = 0.0
            
    # Processa linhas de movimentação
    linhas = text_full.split('\n')
    transacoes = []
    
    for linha in linhas:
        l = linha.strip()
        # Procura linhas com donativos ou despesas
        # Donativo eletrônico
        if "Donativo eletrônico - Donativo p/ a congregação em Betel" in l:
            m = re.findall(r'(\d+[\.,]\d{2})', l)
            if m:
                v = float(m[-1].replace('.', '').replace(',', '.'))
                transacoes.append({"Tipo": "Entrada", "Categoria": "Donativo em Betel", "Descricao": "Donativo Betel", "Valor": v})
        elif "Donativo eletrônico" in l:
            m = re.findall(r'(\d+[\.,]\d{2})', l)
            if m:
                v = float(m[-1].replace('.', '').replace(',', '.'))
                transacoes.append({"Tipo": "Entrada", "Categoria": "Donativo Eletrônico (Local)", "Descricao": "Donativo Eletrônico", "Valor": v})
        elif "Arranjo de Ônibus" in l or "Arranjo de ônibus" in l:
            if "Pagamento empresa" in l or "devolução" in l:
                continue
            m = re.findall(r'(\d+[\.,]\d{2})', l)
            if m:
                v = float(m[-1].replace('.', '').replace(',', '.'))
                transacoes.append({"Tipo": "Entrada", "Categoria": "Arranjo de Ônibus", "Descricao": "Donativo Ônibus", "Valor": v})
        elif "Aporte para a conta de manutenção" in l or "Aporte manutenção" in l or "Aporte de Manutenção" in l:
            m = re.findall(r'(\d+[\.,]\d{2})', l)
            if m:
                v = float(m[-1].replace('.', '').replace(',', '.'))
                transacoes.append({"Tipo": "Despesa", "Categoria": "Manutenção do Salão", "Descricao": l, "Valor": v})
        elif "Almoço dos voluntários" in l or "alimentação curso de altura" in l:
            m = re.findall(r'(\d+[\.,]\d{2})', l)
            if m:
                v = float(m[-1].replace('.', '').replace(',', '.'))
                transacoes.append({"Tipo": "Despesa", "Categoria": "Manutenção / Voluntários", "Descricao": l, "Valor": v})
        elif "Ajuda para o circuito" in l:
            m = re.findall(r'(\d+[\.,]\d{2})', l)
            if m:
                v = float(m[-1].replace('.', '').replace(',', '.'))
                transacoes.append({"Tipo": "Despesa", "Categoria": "Circuito", "Descricao": l, "Valor": v})
        elif "Resolução mensal" in l:
            m = re.findall(r'(\d+[\.,]\d{2})', l)
            if m:
                v = float(m[-1].replace('.', '').replace(',', '.'))
                transacoes.append({"Tipo": "Despesa", "Categoria": "Resolução Obra Mundial", "Descricao": "Resolução Obra Mundial", "Valor": v})
        elif "Plano Anual Zoom" in l:
            m = re.findall(r'(\d+[\.,]\d{2})', l)
            if m:
                v = float(m[-1].replace('.', '').replace(',', '.'))
                transacoes.append({"Tipo": "Despesa", "Categoria": "Tecnologia / Zoom", "Descricao": l, "Valor": v})
        elif "Impressão de convites" in l:
            m = re.findall(r'(\d+[\.,]\d{2})', l)
            if m:
                v = float(m[-1].replace('.', '').replace(',', '.'))
                transacoes.append({"Tipo": "Despesa", "Categoria": "Publicações / Convites", "Descricao": l, "Valor": v})
        elif "DONATIVO PARA ESCOLA DE PIONEIROS" in l:
            m = re.findall(r'(\d+[\.,]\d{2})', l)
            if m:
                v = float(m[-1].replace('.', '').replace(',', '.'))
                transacoes.append({"Tipo": "Despesa", "Categoria": "Escola de Pioneiros", "Descricao": l, "Valor": v})
        elif "Pagamento empresa de ônibus" in l:
            m = re.findall(r'(\d+[\.,]\d{2})', l)
            if m:
                v = float(m[-1].replace('.', '').replace(',', '.'))
                transacoes.append({"Tipo": "Despesa", "Categoria": "Transporte / Ônibus", "Descricao": l, "Valor": v})
        elif "devolução passagem" in l:
            m = re.findall(r'(\d+[\.,]\d{2})', l)
            if m:
                v = float(m[-1].replace('.', '').replace(',', '.'))
                transacoes.append({"Tipo": "Despesa", "Categoria": "Devolução Passagem", "Descricao": l, "Valor": v})

        # Donativos de Caixas (Congregação)
        if re.search(r'Congregação\s+\|\s*(\d+[\.,]\d{2})', l) or re.search(r'(\d+[\.,]\d{2})\s+C', l):
            m = re.findall(r'(\d+[\.,]\d{2})', l)
            if m:
                v = float(m[0].replace('.', '').replace(',', '.'))
                if v > 0:
                    transacoes.append({"Tipo": "Entrada", "Categoria": "Caixa Local (Congregação)", "Descricao": "Caixa da Congregação", "Valor": v})

    df = pd.DataFrame(transacoes)
    return mes_str, ano_str, saldo_disp, df

# Sidebar
st.sidebar.title("📁 Importação S-26")
st.sidebar.info("Faça upload dos PDFs das Folhas de Contas (S-26) geradas no JW Hub.")
uploaded_files = st.sidebar.file_uploader("Selecione os relatórios em PDF", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    dados_meses = {}
    for f in uploaded_files:
        bytes_data = f.read()
        m, a, saldo, df_t = parse_s26_pdf(bytes_data)
        chave = f"{m.capitalize()} {a}"
        num_m = MONTH_ORDER.get(m, 12)
        dados_meses[chave] = {
            "mes": m,
            "ano": a,
            "ordem": int(a) * 100 + num_m,
            "saldo_final": saldo,
            "transacoes": df_t
        }
    
    # Ordena cronologicamente
    meses_ordenados = sorted(dados_meses.keys(), key=lambda x: dados_meses[x]["ordem"])
    
    aba1, aba2, aba3 = st.tabs(["📢 Anúncio S-30 (Leitura)", "📊 Visão Mensal Detalhada", "📈 Análise Anual & Tendências"])
    
    with aba1:
        st.subheader("📢 Anúncio Mensal sobre as Contas da Congregação (S-30)")
        mes_selecionado = st.selectbox("Selecione o mês para o Fechamento / Leitura:", meses_ordenados, index=len(meses_ordenados)-1)
        
        info_m = dados_meses[mes_selecionado]
        df_mes = info_m["transacoes"]
        
        # Filtra entradas e despesas
        entradas_cong = df_mes[df_mes["Tipo"] == "Entrada"]["Valor"].sum()
        despesas_df = df_mes[df_mes["Tipo"] == "Despesa"]
        despesas_cong = despesas_df["Valor"].sum()
        saldo_fim = info_m["saldo_final"]
        
        # Agrupamento das despesas discriminadas
        desp_agrupadas = despesas_df.groupby("Categoria")["Valor"].sum().reset_index()
        descritivo_despesas = []
        for _, row in desp_agrupadas.iterrows():
            descritivo_despesas.append(f"• **{row['Categoria']}**: R$ {row['Valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        texto_discriminado = "\n".join(descritivo_despesas)
        
        st.markdown(f"""
        <div class="s30-box">
            <h4>Anúncio mensal sobre as contas da congregação (S-30)</h4>
            <p><strong>Instruções:</strong> O anúncio deve ser lido para a congregação na segunda semana de cada mês, na reunião do meio de semana. Se o anúncio não puder ser feito (por exemplo, se a congregação tiver assembleia ou congresso), então ele pode ser feito na semana seguinte. Depois de o anúncio ter sido lido, a página 1 deste relatório deve ser colocada no quadro de anúncios.</p>
            <hr style="border: 0; border-top: 1px solid #d4b85c;">
            <h5><strong>Leia para a congregação:</strong></h5>
            <p style="font-size: 16px; line-height: 1.6;">
            Uma cópia do Relatório Mensal de Contas da Congregação do mês de <strong>{info_m['mes'].capitalize()} de {info_m['ano']}</strong> será colocada no quadro de anúncios. 
            Em resumo, a congregação recebeu um total de <strong>R$ {entradas_cong:,.2f}</strong>. 
            As despesas da congregação para o mês deram um total de <strong>R$ {despesas_cong:,.2f}</strong>, distribuídas nas seguintes necessidades:<br>
            </p>
        </div>
        """.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)
        
        st.markdown(texto_discriminado)
        
        st.markdown(f"""
        <div class="s30-box" style="margin-top: 10px;">
            <p style="font-size: 16px;">Isso deixa no final do mês um saldo de <strong>R$ {saldo_fim:,.2f}</strong>.</p>
        </div>
        """.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)
        
        st.button("📋 Copiar Anúncio", on_click=lambda: st.success("Texto pronto para ser lido na reunião!"))

    with aba2:
        st.subheader(f"Análise das Contas - {mes_selecionado}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Entradas Totais", f"R$ {entradas_cong:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col2.metric("Despesas Operacionais", f"R$ {despesas_cong:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col3.metric("Saldo Disponível Final", f"R$ {saldo_fim:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        c_graf1, c_graf2 = st.columns(2)
        with c_graf1:
            st.markdown("##### Entradas por Categoria")
            ent_grp = df_mes[df_mes["Tipo"] == "Entrada"].groupby("Categoria")["Valor"].sum().reset_index()
            if not ent_grp.empty:
                fig_in = px.pie(ent_grp, names="Categoria", values="Valor", hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
                st.plotly_chart(fig_in, use_container_width=True)
            else:
                st.write("Sem registros de entrada detalhados.")
                
        with c_graf2:
            st.markdown("##### Despesas por Categoria")
            if not desp_agrupadas.empty:
                fig_out = px.pie(desp_agrupadas, names="Categoria", values="Valor", hole=0.4, color_discrete_sequence=px.colors.sequential.Burg)
                st.plotly_chart(fig_out, use_container_width=True)
            else:
                st.write("Sem despesas no mês.")
                
        st.markdown("##### Extrato Analítico do Mês")
        st.dataframe(df_mes, use_container_width=True)

    with aba3:
        st.subheader("📈 Evolução Anual Consolidada")
        resumo_anual = []
        for k in meses_ordenados:
            inf = dados_meses[k]
            df_i = inf["transacoes"]
            e_tot = df_i[df_i["Tipo"] == "Entrada"]["Valor"].sum()
            d_tot = df_i[df_i["Tipo"] == "Despesa"]["Valor"].sum()
            resumo_anual.append({
                "Mês": k,
                "Entradas": e_tot,
                "Despesas": d_tot,
                "Saldo Final": inf["saldo_final"]
            })
        df_anual = pd.DataFrame(resumo_anual)
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=df_anual["Mês"], y=df_anual["Entradas"], name="Entradas (R$)", marker_color="#2b5c8f"))
        fig_bar.add_trace(go.Bar(x=df_anual["Mês"], y=df_anual["Despesas"], name="Despesas (R$)", marker_color="#d9534f"))
        fig_bar.update_layout(title="Comparativo Mensal: Entradas vs Despesas", barmode="group")
        st.plotly_chart(fig_bar, use_container_width=True)
        
        fig_line = px.line(df_anual, x="Mês", y="Saldo Final", title="Evolução do Saldo Disponível ao Longo do Ano", markers=True)
        fig_line.update_traces(line_color="#27ae60", line_width=3)
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.dataframe(df_anual.style.format({"Entradas": "R$ {:,.2f}", "Despesas": "R$ {:,.2f}", "Saldo Final": "R$ {:,.2f}"}), use_container_width=True)

else:
    st.info("👆 Por favor, envie os PDFs das Folhas de Contas (S-26) na barra lateral para começar a análise.")
