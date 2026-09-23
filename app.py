import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Configuração da página Web
st.set_page_config(
    page_title="Mercadinho de Betim",
    page_icon="🛒",
    layout="wide"
)

DB_PATH = "historico_mercadinho.db"


# --- FUNÇÕES DE CONEXÃO E INICIALIZAÇÃO DO BANCO ---
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def inicializar_banco():
    conn = get_connection()
    cursor = conn.cursor()
    # Tabela Histórico (Compras e Vendas)
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
    # Tabela Despesas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            descricao TEXT,
            valor REAL,
            data_registro TEXT
        )
    ''')
    # Tabela Estoque Caixa
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estoque_caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            saldo REAL
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM estoque_caixa")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO estoque_caixa (id, saldo) VALUES (1, 0.0)")

    conn.commit()
    conn.close()


inicializar_banco()

# --- BARRA LATERAL (MENU PRINCIPAL) ---
st.sidebar.title("🛒 Mercadinho de Betim")
st.sidebar.markdown("---")
pagina = st.sidebar.radio(
    "Navegação do Sistema:",
    ["🏠 Início / Lançamentos", "📊 Balanço Geral", "💸 Gestão de Despesas", "📈 Resumo Financeiro"]
)


# Saldo do Estoque no Menu Lateral
def obter_saldo_estoque():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT saldo FROM estoque_caixa WHERE id = 1")
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0.0


saldo_est = obter_saldo_estoque()
st.sidebar.markdown("---")
st.sidebar.metric("💵 Saldo em Estoque", f"R$ {saldo_est:.2f}")

# ==============================================================================
# 1. PÁGINA: INÍCIO / LANÇAMENTOS (Substitui o main.py)
# ==============================================================================
if pagina == "🏠 Início / Lançamentos":
    st.title("🛒 Lançamento de Compras e Vendas")
    st.write("Registre as movimentações diárias do caixa com salvamento automático.")

    col_form, col_saldo = st.columns([2, 1])

    with col_form:
        with st.form("form_lancamento", clear_on_submit=True):
            st.subheader("Novo Registro")
            col1, col2 = st.columns(2)
            tipo = col1.selectbox("Tipo de Operação:", ["VENDA", "COMPRA"])
            data_op = col2.date_input("Data:", datetime.now())

            descricao = st.text_input("Descrição / Produto:", placeholder="Ex: Mercadoria geral")
            valor = st.number_input("Valor Total (R$):", min_value=0.0, format="%.2f")

            porcentagem = 0.0
            if tipo == "COMPRA":
                porcentagem = st.number_input("Porcentagem (%):", min_value=0.0, format="%.2f")

            submeter = st.form_submit_button("💾 Salvar Registro")

            if submeter:
                if valor <= 0:
                    st.error("Informe um valor maior que zero!")
                else:
                    dt_str = data_op.strftime("%d/%m/%Y")
                    dt_exp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    if tipo == "COMPRA":
                        perc_str = f"{porcentagem:g}%"
                        if porcentagem > 0:
                            dif = valor / porcentagem
                            dif_str = f"{dif:.2f}"
                        else:
                            dif_str = "0.00"
                    else:
                        perc_str = "-"
                        dif_str = "-"

                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO historico (data, tipo, produto, valor_total, porcentagem, diferenca, data_exportacao)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (dt_str, tipo, descricao, valor, perc_str, dif_str, dt_exp))
                    conn.commit()
                    conn.close()
                    st.success(f"{tipo.capitalize()} gravada com sucesso!")
                    st.rerun()

    with col_saldo:
        st.subheader("⚙️ Caixa / Estoque")
        novo_saldo = st.number_input("Atualizar Saldo em Estoque (R$):", value=saldo_est, format="%.2f")
        if st.button("🔄 Atualizar Estoque"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE estoque_caixa SET saldo = ? WHERE id = 1", (novo_saldo,))
            conn.commit()
            conn.close()
            st.success("Estoque atualizado!")
            st.rerun()


# ==============================================================================
# 2. PÁGINA: BALANÇO GERAL (Substitui a janela_balanco.py)
# ==============================================================================
elif pagina == "📊 Balanço Geral":
    st.title("📊 Balanço Geral de Lançamentos")

    # Filtros
    col_f1, col_f2, col_f3 = st.columns(3)
    modo_vis = col_f1.radio("Visualizar:", ["Apenas Hoje", "Filtrar por Período", "Mostrar Tudo"], horizontal=True)

    conn = get_connection()
    hoje_str = datetime.now().strftime("%d/%m/%Y")

    if modo_vis == "Apenas Hoje":
        query = "SELECT id, data, tipo, produto, valor_total, porcentagem, diferenca, data_exportacao FROM historico WHERE (data LIKE ? OR data_exportacao LIKE ?) ORDER BY id DESC"
        df = pd.read_sql_query(query, conn, params=(f"%{hoje_str}%", f"%{hoje_str}%"))
    elif modo_vis == "Mostrar Tudo":
        query = "SELECT id, data, tipo, produto, valor_total, porcentagem, diferenca, data_exportacao FROM historico ORDER BY id DESC"
        df = pd.read_sql_query(query, conn)
    else:
        tipo_f = col_f2.selectbox("Tipo:", ["TODOS", "VENDA", "COMPRA"])
        ano_f = col_f3.text_input("Ano (Ex: 2026):", value="2026")

        query = "SELECT id, data, tipo, produto, valor_total, porcentagem, diferenca, data_exportacao FROM historico WHERE 1=1"
        params = []
        if tipo_f != "TODOS":
            query += " AND UPPER(tipo) = ?"
            params.append(tipo_f)
        if ano_f:
            query += " AND (data LIKE ? OR data_exportacao LIKE ?)"
            params.append(f"%{ano_f}%")
            params.append(f"%{ano_f}%")
        query += " ORDER BY id DESC"
        df = pd.read_sql_query(query, conn, params=params)

    conn.close()

    # Métricas
    vendas = df[df['tipo'] == 'VENDA']['valor_total'].sum() if not df.empty else 0.0
    compras = df[df['tipo'] == 'COMPRA']['valor_total'].sum() if not df.empty else 0.0
    lucro = vendas - compras

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Compras", f"R$ {compras:.2f}")
    m2.metric("Total Vendas", f"R$ {vendas:.2f}")
    m3.metric("Lucro Operacional", f"R$ {lucro:.2f}")

    st.dataframe(df, use_container_width=True)


# ==============================================================================
# 3. PÁGINA: GESTÃO DE DESPESAS (Substitui a janela_despesas.py)
# ==============================================================================
elif pagina == "💸 Gestão de Despesas":
    st.title("💸 Controle de Despesas")

    with st.expander("➕ Cadastrar Nova Despesa", expanded=True):
        with st.form("form_despesa", clear_on_submit=True):
            col1, col2 = st.columns(2)
            data_d = col1.date_input("Data:", datetime.now())
            valor_d = col2.number_input("Valor (R$):", min_value=0.0, format="%.2f")
            desc_d = st.text_input("Descrição:")

            if st.form_submit_button("💾 Salvar Despesa"):
                if desc_d and valor_d > 0:
                    dt_str = data_d.strftime("%d/%m/%Y")
                    dt_reg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO despesas (data, descricao, valor, data_registro) VALUES (?, ?, ?, ?)",
                                   (dt_str, desc_d, valor_d, dt_reg))
                    conn.commit()
                    conn.close()
                    st.success("Despesa registada!")
                    st.rerun()
                else:
                    st.error("Preencha a descrição e um valor válido.")

    st.subheader("Histórico de Despesas")
    filtro_d = st.radio("Exibir:", ["Apenas Hoje", "Mostrar Tudo"], horizontal=True)

    conn = get_connection()
    hoje_str = datetime.now().strftime("%d/%m/%Y")

    if filtro_d == "Apenas Hoje":
        df_d = pd.read_sql_query(
            "SELECT id, data, descricao, valor, data_registro FROM despesas WHERE data LIKE ? ORDER BY id DESC", conn,
            params=(f"%{hoje_str}%",))
    else:
        df_d = pd.read_sql_query("SELECT id, data, descricao, valor, data_registro FROM despesas ORDER BY id DESC",
                                 conn)

    conn.close()

    st.dataframe(df_d, use_container_width=True)
    st.metric("Total em Despesas", f"R$ {df_d['valor'].sum() if not df_d.empty else 0.0:.2f}")


# ==============================================================================
# 4. PÁGINA: RESUMO FINANCEIRO (Substitui a janela_resumo.py)
# ==============================================================================
elif pagina == "📈 Resumo Financeiro":
    st.title("📈 Resumo Financeiro Completo")

    col_a, col_m = st.columns(2)
    ano_sel = col_a.text_input("Ano de Análise:", value="2026")
    mes_sel = col_m.selectbox("Mês:", ["TODOS", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"])

    conn = get_connection()

    # Busca dados
    df_h = pd.read_sql_query("SELECT data, tipo, valor_total FROM historico WHERE data LIKE ?", conn,
                             params=(f"%{ano_sel}%",))
    df_dp = pd.read_sql_query("SELECT data, valor FROM despesas WHERE data LIKE ?", conn, params=(f"%{ano_sel}%",))

    conn.close()

    # Processamento dos meses
    meses_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    dados_meses = []

    tot_c, tot_v, tot_d = 0.0, 0.0, 0.0

    for idx in range(1, 13):
        m_str = f"{idx:02d}"
        if mes_sel != "TODOS" and mes_sel != m_str:
            continue

        # Compras e Vendas do mês
        v_mes = df_h[(df_h['tipo'] == 'VENDA') & (df_h['data'].str.contains(f"/{m_str}/", na=False))][
            'valor_total'].sum()
        c_mes = df_h[(df_h['tipo'] == 'COMPRA') & (df_h['data'].str.contains(f"/{m_str}/", na=False))][
            'valor_total'].sum()
        d_mes = df_dp[df_dp['data'].str.contains(f"/{m_str}/", na=False)]['valor'].sum()

        l_bruto = v_mes - c_mes
        l_liquido = v_mes - c_mes - d_mes
        est_corrigido = saldo_est + l_liquido

        tot_v += v_mes
        tot_c += c_mes
        tot_d += d_mes

        dados_meses.append({
            "Mês": meses_nomes[idx - 1],
            "Compras (R$)": c_mes,
            "Vendas (R$)": v_mes,
            "Despesas (R$)": d_mes,
            "Lucro Bruto (R$)": l_bruto,
            "Lucro Líquido (R$)": l_liquido,
            "Estoque Corrigido (R$)": est_corrigido
        })

    df_resumo = pd.DataFrame(dados_meses)

    tot_l_liquido = tot_v - tot_c - tot_d
    tot_est_corrigido = saldo_est + tot_l_liquido

    # Exibição de Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Totais Vendas", f"R$ {tot_v:.2f}")
    c2.metric("Totais Compras", f"R$ {tot_c:.2f}")
    c3.metric("Totais Despesas", f"R$ {tot_d:.2f}")
    c4.metric("Lucro Líquido", f"R$ {tot_l_liquido:.2f}")

    st.markdown(f"### 📊 Estoque Corrigido Final: **R$ {tot_est_corrigido:.2f}**")

    st.dataframe(df_resumo, use_container_width=True)

    # Gráfico Matplotlib
    if not df_resumo.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df_resumo["Mês"], df_resumo["Vendas (R$)"], marker='o', color='#2e7d32', label='Vendas')
        ax.plot(df_resumo["Mês"], df_resumo["Compras (R$)"], marker='o', color='#d32f2f', label='Compras')
        ax.plot(df_resumo["Mês"], df_resumo["Despesas (R$)"], marker='o', color='#e65100', label='Despesas')
        ax.set_title(f"Variação Financeira - {ano_sel}")
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        st.pyplot(fig)