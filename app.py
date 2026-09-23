import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt

# Configuração da página
st.set_page_config(
    page_title="Mercadinho de Betim",
    page_icon="🛒",
    layout="wide"
)

DB_PATH = "historico_mercadinho.db"

# --- BANCO DE DADOS ---
def inicializar_banco_dados():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            produto TEXT,
            valor_total REAL,
            porcentagem TEXT,
            diferenca TEXT,
            data_exportacao TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estoque_caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            saldo REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            descricao TEXT,
            valor REAL,
            data_registro TEXT
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM estoque_caixa")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO estoque_caixa (saldo) VALUES (0.0)")
    conn.commit()
    conn.close()

def obter_saldo_estoque():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT saldo FROM estoque_caixa WHERE id = 1")
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0.0

def atualizar_saldo_estoque(novo_saldo):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE estoque_caixa SET saldo = ? WHERE id = 1", (novo_saldo,))
    conn.commit()
    conn.close()

def salvar_transacao(item):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    dt_reg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO historico (data, tipo, produto, valor_total, porcentagem, diferenca, data_exportacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (item["data"], item["tipo"], item["produto"], item["valor_total"], item["porcentagem"], item["diferenca"], dt_reg))
    conn.commit()
    conn.close()

def deletar_transacao(db_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM historico WHERE id = ?", (db_id,))
    conn.commit()
    conn.close()

def salvar_despesa(data_str, desc, valor):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    dt_reg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO despesas (data, descricao, valor, data_registro)
        VALUES (?, ?, ?, ?)
    ''', (data_str, desc, valor, dt_reg))
    conn.commit()
    conn.close()

def deletar_despesa(db_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM despesas WHERE id = ?", (db_id,))
    conn.commit()
    conn.close()

# Inicializa as tabelas do SQLite
inicializar_banco_dados()

# --- CABEÇALHO ---
st.title("🛒 Mercadinho de Betim")
st.subheader("Sistema de Gestão Financeira")

# Menu Principal em Abas
aba_lancamentos, aba_despesas, aba_balanco, aba_estoque, aba_resumo, aba_backup = st.tabs([
    "📦 Lançar Compra / Venda", 
    "💸 Despesas", 
    "📊 Balanço Geral", 
    "💵 Estoque Caixa", 
    "📈 Resumo Anual / Gráficos",
    "💾 Backup / Dados"
])

# --- ABA 1: LANÇAMENTOS (COMPRA / VENDA) ---
with aba_lancamentos:
    hoje_str = datetime.now().strftime("%d/%m/%Y")
    
    # Busca lançamentos do dia no banco de dados
    conn = sqlite3.connect(DB_PATH)
    df_hoje = pd.read_sql_query("SELECT tipo, valor_total, porcentagem, diferenca FROM historico WHERE data = ?", conn, params=(hoje_str,))
    conn.close()

    # Cálculo dos indicadores do dia atual
    vendas_hoje = df_hoje[df_hoje["tipo"] == "VENDA"]["valor_total"].sum() if not df_hoje.empty else 0.0
    compras_hoje = df_hoje[df_hoje["tipo"] == "COMPRA"]["valor_total"].sum() if not df_hoje.empty else 0.0
    lucro_hoje = vendas_hoje - compras_hoje

    soma_porcentagem_hoje = 0.0
    soma_diferenca_hoje = 0.0

    if not df_hoje.empty:
        for _, row in df_hoje.iterrows():
            # Converte porcentagem (ex: '10%') para float
            p_str = str(row["porcentagem"]).replace("%", "").strip()
            if p_str != "-":
                try:
                    soma_porcentagem_hoje += float(p_str)
                except ValueError:
                    pass

            # Converte diferença para float
            d_str = str(row["diferenca"]).strip()
            if d_str != "-":
                try:
                    soma_diferenca_hoje += float(d_str)
                except ValueError:
                    pass

    # Exibição do Painel Resumo do Dia
    st.markdown(f"### 📅 Resumo do Dia de Hoje ({hoje_str})")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🛒 Vendas do Dia", f"R$ {vendas_hoje:.2f}")
    m2.metric("📦 Compras do Dia", f"R$ {compras_hoje:.2f}")
    m3.metric("💡 Lucro do Dia", f"R$ {lucro_hoje:.2f}")
    m4.metric("📊 Soma Porcentagens", f"{soma_porcentagem_hoje:g}%")
    m5.metric("⚖️ Soma Diferenças", f"R$ {soma_diferenca_hoje:.2f}")

    st.divider()

    st.header("Novo Lançamento")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛒 Lançar Venda")
        with st.form("form_venda", clear_on_submit=True):
            dt_venda = st.date_input("Data da Venda", datetime.now(), key="dt_venda")
            val_venda = st.number_input("Valor Bruto (R$)", min_value=0.01, step=1.0, key="val_venda")
            sub_venda = st.form_submit_button("Salvar Venda", type="primary")
            
            if sub_venda:
                item = {
                    "data": dt_venda.strftime("%d/%m/%Y"),
                    "tipo": "VENDA",
                    "produto": "Venda Avulsa",
                    "valor_total": val_venda,
                    "porcentagem": "-",
                    "diferenca": "-"
                }
                salvar_transacao(item)
                st.success("Venda registrada com sucesso!")
                st.rerun()

    with col2:
        st.subheader("📦 Lançar Compra")
        with st.form("form_compra", clear_on_submit=True):
            dt_compra = st.date_input("Data da Compra", datetime.now(), key="dt_compra")
            val_compra = st.number_input("Valor Bruto (R$)", min_value=0.01, step=1.0, key="val_compra")
            perc_compra = st.number_input("Porcentagem (%)", min_value=0.0, step=0.5, key="perc_compra")
            sub_compra = st.form_submit_button("Salvar Compra", type="primary")
            
            if sub_compra:
                if perc_compra > 0:
                    dif = val_compra / perc_compra
                    dif_str = f"{dif:.2f}"
                else:
                    dif_str = "0.00"
                
                item = {
                    "data": dt_compra.strftime("%d/%m/%Y"),
                    "tipo": "COMPRA",
                    "produto": "Compra Avulsa",
                    "valor_total": val_compra,
                    "porcentagem": f"{perc_compra:g}%",
                    "diferenca": dif_str
                }
                salvar_transacao(item)
                st.success("Compra registrada com sucesso!")
                st.rerun()

# --- ABA 2: DESPESAS ---
with aba_despesas:
    st.header("Controlador de Despesas")
    
    with st.form("form_despesa", clear_on_submit=True):
        col_d1, col_d2, col_d3 = st.columns([1, 2, 1])
        with col_d1:
            dt_desp = st.date_input("Data", datetime.now())
        with col_d2:
            desc_desp = st.text_input("Descrição da Despesa")
        with col_d3:
            val_desp = st.number_input("Valor (R$)", min_value=0.01, step=1.0)
            
        sub_desp = st.form_submit_button("➕ Cadastrar Despesa")
        if sub_desp:
            if desc_desp.strip():
                salvar_despesa(dt_desp.strftime("%d/%m/%Y"), desc_desp, val_desp)
                st.success("Despesa cadastrada!")
                st.rerun()
            else:
                st.error("Informe uma descrição.")

    st.divider()
    st.subheader("Histórico de Despesas")
    
    conn = sqlite3.connect(DB_PATH)
    df_desp = pd.read_sql_query("SELECT id, data, descricao, valor, data_registro FROM despesas ORDER BY id DESC", conn)
    conn.close()

    if not df_desp.empty:
        st.dataframe(df_desp, use_container_width=True)
        st.metric("Total em Despesas", f"R$ {df_desp['valor'].sum():.2f}")
        
        id_del = st.number_input("ID da Despesa para Excluir", min_value=1, step=1)
        if st.button("🗑️ Excluir Despesa por ID"):
            deletar_despesa(id_del)
            st.success(f"Despesa #{id_del} excluída!")
            st.rerun()
    else:
        st.info("Nenhuma despesa cadastrada.")

# --- ABA 3: BALANÇO GERAL ---
with aba_balanco:
    st.header("📊 Balanço Geral de Lançamentos")
    
    conn = sqlite3.connect(DB_PATH)
    df_hist = pd.read_sql_query("SELECT id, data, tipo, produto, valor_total, porcentagem, diferenca, data_exportacao FROM historico ORDER BY id DESC", conn)
    conn.close()

    if not df_hist.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            tipo_filtro = st.selectbox("Filtrar por Tipo", ["TODOS", "VENDA", "COMPRA"])
        
        df_exibir = df_hist.copy()
        if tipo_filtro != "TODOS":
            df_exibir = df_exibir[df_exibir["tipo"] == tipo_filtro]
            
        st.dataframe(df_exibir, use_container_width=True)
        
        tot_vendas = df_hist[df_hist["tipo"] == "VENDA"]["valor_total"].sum()
        tot_compras = df_hist[df_hist["tipo"] == "COMPRA"]["valor_total"].sum()
        lucro = tot_vendas - tot_compras
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Vendas", f"R$ {tot_vendas:.2f}")
        c2.metric("Total Compras", f"R$ {tot_compras:.2f}")
        c3.metric("Lucro Bruto", f"R$ {lucro:.2f}")

        id_hist_del = st.number_input("ID do Lançamento para Excluir", min_value=1, step=1, key="del_hist")
        if st.button("🗑️ Excluir Lançamento por ID"):
            deletar_transacao(id_hist_del)
            st.success(f"Lançamento #{id_hist_del} excluído!")
            st.rerun()
    else:
        st.info("Nenhum lançamento encontrado.")

# --- ABA 4: ESTOQUE CAIXA ---
with aba_estoque:
    st.header("💵 Dinheiro em Estoque Caixa")
    
    saldo_atual = obter_saldo_estoque()
    st.metric("Saldo Atual em Estoque", f"R$ {saldo_atual:.2f}")
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        valor_alterar = st.number_input("Valor para Alterar (R$)", min_value=0.01, step=1.0)
    
    with col_e2:
        st.write("Ações:")
        if st.button("➕ Aumentar Saldo", type="primary"):
            atualizar_saldo_estoque(saldo_atual + valor_alterar)
            st.success("Saldo aumentado!")
            st.rerun()
        if st.button("➖ Diminuir Saldo"):
            atualizar_saldo_estoque(saldo_atual - valor_alterar)
            st.success("Saldo diminuído!")
            st.rerun()

# --- ABA 5: RESUMO ANUAL / GRÁFICOS ---
with aba_resumo:
    st.header("📈 Resumo Financeiro & Gráfico")
    
    ano_sel = st.text_input("Consultar Ano", datetime.now().strftime("%Y"))
    
    conn = sqlite3.connect(DB_PATH)
    df_h = pd.read_sql_query("SELECT data, tipo, valor_total FROM historico", conn)
    df_d = pd.read_sql_query("SELECT data, valor FROM despesas", conn)
    conn.close()

    meses_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    dados_mes = {i: {"vendas": 0.0, "compras": 0.0, "despesas": 0.0} for i in range(1, 13)}

    for _, row in df_h.iterrows():
        dt = str(row["data"])
        if ano_sel in dt:
            for m in range(1, 13):
                m_str = f"{m:02d}"
                if f"/{m_str}/" in dt or f"-{m_str}-" in dt:
                    if row["tipo"] == "VENDA":
                        dados_mes[m]["vendas"] += row["valor_total"]
                    else:
                        dados_mes[m]["compras"] += row["valor_total"]
                    break

    for _, row in df_d.iterrows():
        dt = str(row["data"])
        if ano_sel in dt:
            for m in range(1, 13):
                m_str = f"{m:02d}"
                if f"/{m_str}/" in dt or f"-{m_str}-" in dt:
                    dados_mes[m]["despesas"] += row["valor"]
                    break

    lista_resumo = []
    v_list, c_list, d_list = [], [], []
    for m in range(1, 13):
        v = dados_mes[m]["vendas"]
        c = dados_mes[m]["compras"]
        d = dados_mes[m]["despesas"]
        v_list.append(v)
        c_list.append(c)
        d_list.append(d)
        
        lucro_l = v - c - d
        lista_resumo.append({
            "Mês": meses_nomes[m-1],
            "Vendas (R$)": f"R$ {v:.2f}",
            "Compras (R$)": f"R$ {c:.2f}",
            "Despesas (R$)": f"R$ {d:.2f}",
            "Lucro Líquido (R$)": f"R$ {lucro_l:.2f}"
        })

    st.dataframe(pd.DataFrame(lista_resumo), use_container_width=True)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(meses_nomes, v_list, marker='o', color='#2e7d32', label='Vendas (R$)')
    ax.plot(meses_nomes, c_list, marker='o', color='#d32f2f', label='Compras (R$)')
    ax.plot(meses_nomes, d_list, marker='o', color='#e65100', label='Despesas (R$)')
    ax.set_title(f"Evolução Financeira - {ano_sel}")
    ax.set_ylabel("Valor (R$)")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()

    st.pyplot(fig)

# --- ABA 6: BACKUP E RESTAURAÇÃO ---
with aba_backup:
    st.header("💾 Backup e Restauração do Banco de Dados")
    st.write("Faça o download do seu banco de dados regularmente para manter uma cópia de segurança local.")
    
    col_b1, col_b2 = st.columns(2)
    
    with col_b1:
        st.subheader("📥 Baixar Cópia de Segurança")
        try:
            with open(DB_PATH, "rb") as file:
                st.download_button(
                    label="Fazer Download do Banco de Dados (.db)",
                    data=file,
                    file_name=f"backup_mercadinho_{datetime.now().strftime('%Y_%m_%d')}.db",
                    mime="application/x-sqlite3",
                    type="primary"
                )
        except FileNotFoundError:
            st.error("Arquivo de banco de dados ainda não foi criado.")

    with col_b2:
        st.subheader("📤 Restaurar Banco de Dados")
        uploaded_file = st.file_uploader("Envie um arquivo .db de backup antigo", type=["db"])
        
        if uploaded_file is not None:
            if st.button("⚠️ Confirmar Restauração", type="primary"):
                with open(DB_PATH, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Banco de dados restaurado com sucesso!")
                st.rerun()
