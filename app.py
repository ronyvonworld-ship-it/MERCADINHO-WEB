import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import dropbox
from dropbox.exceptions import ApiError

# Configuração da página
st.set_page_config(
    page_title="Mercadinho Nova Esperança",
    page_icon="🛒",
    layout="wide"
)

DB_PATH = "historico_mercadinho.db"

# --- CONFIGURAÇÃO DO DROPBOX ---
DROPBOX_TOKEN = "sl.u.AGxUKmF13Svtu1X4Zo3uUpq1hAx_AF9fj8mTmJP77ixA2H1jL8qf80FyqqBVWR6ePcdPzsLuh6bVvnh0Td0sQiqaXHGRqHOhsBZAHvDjz5O35cD0Dj55GLvJ35aKvWfH_rLVlCD9TtbqLmzhT5bD1yA52rDbw1MC6UJ9IxOZCXdoGhLo_oOaTTW0ZQCTPLAKnlXxXVL2BpKmma9mJpV-TgfRw-w8jeCb48kdguJKIaLnFmh003AenmmNW9aSLQzNVLGWuGtx78dHvlLx53P95H-I0hUFfHnmW_RJ2amDUAGqRHxAmfrbsSTu4AjERkwA3kl_WzWa-5pXwEyBf2fDT-sSxdFM54BDcs1I-GCy7cu_Z4vb2htGD_SQTBPiPEHoP7ihIAi10Ew1DbfhSKMYWILWNxcSKvnGYb0TXmovqzXuQxEJ26-Nutb7X54sFNSB_9J4RYr-8VppYSQ-Xl9Nnb6ZtQ1PFx9TWSnYHAKRg-CrYjsmQbBiHvaI-lWJjt7Pk50ZJLDhGV1jycXXYtK_m_wK0UdZDvXPJAnAChknlv63JPfEDgAIvI916AyoBTi-RDSj0IGNaDDhoi6384riBNijPMrCpaIC03gOOiAhTHJeUcH0yBRdtuyqqbbZdfg8oHyTE8MSJiHZ7acHuMEMBRl-wPEo4jwzHbu2EStYNBaEnZfhDroNiqeb0_tVgmY66oEAo9eA1b1h1T5WxX6JlAQS2JFzKv6MOggpG6B2mNYt4uQrGYi4vGMo8T3WS08zWMo1yBWiHm9nFZmnsjD5eCA4cR_W10G4h5jmejZTZu-J49YFfJH_R784xqQAU_Gv2SO7PTrl4cZjTFoJu-opx3kbP5HA0_d4ybf_LFUNtbeI8viPkLFfxPD_oqM-ejYFPo5T8ZUC8RKcr5dnTA-cEyLUhA1Pl4D6HV75wWLHb3x9Su-0SpihlHr3Ct9MRGY33x9jWqmX7A9tbakpirMJPRvKTCeV7TjHhL-UkzuX_vZwOpnBhdgdC5Pu_y9bNyunlkFu1rvOjVPEAoWEmrHzc6kjWrgHml-xqoilB-hFgMomwMy9sxZnQubwoq4Vlag7mywDp2rr-ZeR9QqakuV_bmyqO2WKo5fJUgPW1Tgc9vZhfP9RWBf07or0I7cy87GmtZdAVViau8clvc8B6Ic3-n3lSMJi__BBtNA5pNJA0SWGAr0MKQhNn-Gi9SD47IuUsyALE9-nMuezYXlrzxY_duosbhzF8YwN8Y1Ph99cZtwbYzls3IOLQBAkzGuLUdZSE2npnANZbKf0gXyxl2ZZRGP1d29ye6NBtSAlgGZpv9KeQwGWkkSqY-sISxOzaZ5czry5ZEmUpW_m9uQGm0nzEH95ILMrYu0idLfDG3-JTEBnjOKX_ZLr9qKjEO_GQNXBKlrS_-nOc8yp-oOD0sT0Y23SBS1eyM-8E_8vIls26Iekiw"
DROPBOX_FILE_PATH = "/historico_mercadinho.db"

def carregar_db_do_dropbox():
    try:
        dbx = dropbox.Dropbox(DROPBOX_TOKEN)
        metadata, response = dbx.files_download(path=DROPBOX_FILE_PATH)
        with open(DB_PATH, "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Aviso: Não foi possível carregar o banco de dados do Dropbox: {e}")
        return False

def salvar_db_no_dropbox():
    try:
        dbx = dropbox.Dropbox(DROPBOX_TOKEN)
        with open(DB_PATH, "rb") as f:
            dbx.files_upload(f.read(), DROPBOX_FILE_PATH, mode=dropbox.files.WriteMode.overwrite)
        return True
    except Exception as e:
        print(f"Erro ao enviar banco de dados para o Dropbox: {e}")
        return False

# Carrega a versão mais recente do Dropbox na inicialização
if "db_carregado" not in st.session_state:
    carregar_db_do_dropbox()
    st.session_state["db_carregado"] = True

# --- BANCO DE DADOS LOCAL ---
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
    salvar_db_no_dropbox()

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
    salvar_db_no_dropbox()

def atualizar_transacao(db_id, data_str, valor_total, porcentagem_str, diferenca_str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE historico
        SET data = ?, valor_total = ?, porcentagem = ?, diferenca = ?
        WHERE id = ?
    ''', (data_str, valor_total, porcentagem_str, diferenca_str, db_id))
    conn.commit()
    conn.close()
    salvar_db_no_dropbox()

def deletar_transacao(db_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM historico WHERE id = ?", (db_id,))
    conn.commit()
    conn.close()
    salvar_db_no_dropbox()

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
    salvar_db_no_dropbox()

def atualizar_despesa(db_id, desc, valor):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE despesas
        SET descricao = ?, valor = ?
        WHERE id = ?
    ''', (desc, valor, db_id))
    conn.commit()
    conn.close()
    salvar_db_no_dropbox()

def deletar_despesa(db_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM despesas WHERE id = ?", (db_id,))
    conn.commit()
    conn.close()
    salvar_db_no_dropbox()

# Inicializa as tabelas do SQLite
inicializar_banco_dados()

# --- MODAIS DE CONFIRMAÇÃO (st.dialog) ---
@st.dialog("⚠️ Confirmar Exclusão de Despesa")
def modal_confirmar_deletar_despesa(id_despesa, desc):
    st.write(f"Tem certeza que deseja excluir permanentemente a despesa **#{id_despesa} - {desc}**?")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("🔴 Sim, Excluir", type="primary", use_container_width=True):
            deletar_despesa(id_despesa)
            st.success("Despesa excluída com sucesso!")
            st.rerun()
    with col_c2:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()

@st.dialog("⚠️ Confirmar Exclusão de Lançamento")
def modal_confirmar_deletar_transacao(id_transacao, tipo, valor):
    st.write(f"Tem certeza que deseja excluir o lançamento **#{id_transacao}** ({tipo} de R$ {valor:.2f})?")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("🔴 Sim, Excluir", type="primary", use_container_width=True):
            deletar_transacao(id_transacao)
            st.success("Lançamento excluído com sucesso!")
            st.rerun()
    with col_c2:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()

@st.dialog("⚠️ Confirmar Restauração de Backup")
def modal_confirmar_restauracao(uploaded_file):
    st.warning("Atenção! Esta ação irá sobrescrever o banco de dados atual com o arquivo de backup enviado.")
    st.write("Deseja realmente continuar?")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("🔴 Sim, Restaurar", type="primary", use_container_width=True):
            with open(DB_PATH, "wb") as f:
                f.write(uploaded_file.getbuffer())
            salvar_db_no_dropbox()
            st.success("Banco de dados restaurado com sucesso!")
            st.rerun()
    with col_c2:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()

# --- CABEÇALHO ---
st.title("🛒 Mercadinho Nova Esperança")
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
    col_top1, col_top2 = st.columns([2, 1])
    with col_top1:
        st.markdown("### 📅 Resumo Financeiro Diário")
    with col_top2:
        dt_resumo_sel = st.date_input("Selecione a Data do Resumo", datetime.now(), key="dt_resumo_dia")
        
    data_resumo_str = dt_resumo_sel.strftime("%d/%m/%Y")
    
    conn = sqlite3.connect(DB_PATH)
    df_dia = pd.read_sql_query("SELECT tipo, valor_total, porcentagem, diferenca FROM historico WHERE data = ?", conn, params=(data_resumo_str,))
    conn.close()

    vendas_dia = df_dia[df_dia["tipo"] == "VENDA"]["valor_total"].sum() if not df_dia.empty else 0.0
    compras_dia = df_dia[df_dia["tipo"] == "COMPRA"]["valor_total"].sum() if not df_dia.empty else 0.0
    lucro_dia = vendas_dia - compras_dia

    soma_porcentagem_dia = 0.0
    soma_diferenca_dia = 0.0

    if not df_dia.empty:
        for _, row in df_dia.iterrows():
            p_str = str(row["porcentagem"]).replace("%", "").strip()
            if p_str != "-":
                try:
                    soma_porcentagem_dia += float(p_str)
                except ValueError:
                    pass

            d_str = str(row["diferenca"]).strip()
            if d_str != "-":
                try:
                    soma_diferenca_dia += float(d_str)
                except ValueError:
                    pass

    st.caption(f"Exibindo dados do dia: **{data_resumo_str}**")
    m1, m2, m3, m4, m5 = st.columns(5)
    
    m1.markdown(f"**🛒 Vendas do Dia**<h3 style='color: #2e7d32; margin-top:0;'>R$ {vendas_dia:.2f}</h3>", unsafe_allow_html=True)
    m2.markdown(f"**📦 Compras do Dia**<h3 style='color: #c62828; margin-top:0;'>R$ {compras_dia:.2f}</h3>", unsafe_allow_html=True)
    
    cor_lucro = "#2e7d32" if lucro_dia >= 0 else "#c62828"
    m3.markdown(f"**💡 Lucro do Dia**<h3 style='color: {cor_lucro}; margin-top:0;'>R$ {lucro_dia:.2f}</h3>", unsafe_allow_html=True)
    m4.markdown(f"**📊 Soma Porcentagens**<h3 style='color: #1565c0; margin-top:0;'>{soma_porcentagem_dia:g}%</h3>", unsafe_allow_html=True)
    m5.markdown(f"**⚖️ Soma Diferenças**<h3 style='color: #ef6c00; margin-top:0;'>R$ {soma_diferenca_dia:.2f}</h3>", unsafe_allow_html=True)

    st.divider()

    st.header("Novo Lançamento")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛒 Lançar Venda")
        with st.form("form_venda", clear_on_submit=True):
            dt_venda = st.date_input("Data da Venda", datetime.now(), key="dt_venda")
            val_venda = st.number_input("Valor Bruto (R$)", value=None, min_value=0.01, step=1.0, placeholder="Digite o valor...", key="val_venda")
            sub_venda = st.form_submit_button("Salvar Venda", type="primary")
            
            if sub_venda:
                if val_venda is not None and val_venda > 0:
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
                else:
                    st.error("Por favor, digite um valor válido para a venda.")

    with col2:
        st.subheader("📦 Lançar Compra")
        with st.form("form_compra", clear_on_submit=True):
            dt_compra = st.date_input("Data da Compra", datetime.now(), key="dt_compra")
            val_compra = st.number_input("Valor Bruto (R$)", value=None, min_value=0.01, step=1.0, placeholder="Digite o valor...", key="val_compra")
            perc_compra = st.number_input("Porcentagem (%)", value=None, min_value=0.0, step=0.5, placeholder="Digite a porcentagem...", key="perc_compra")
            sub_compra = st.form_submit_button("Salvar Compra", type="primary")
            
            if sub_compra:
                if val_compra is not None and val_compra > 0:
                    p_val = perc_compra if perc_compra is not None else 0.0
                    if p_val > 0:
                        dif = val_compra / p_val
                        dif_str = f"{dif:.2f}"
                    else:
                        dif_str = "0.00"
                    
                    item = {
                        "data": dt_compra.strftime("%d/%m/%Y"),
                        "tipo": "COMPRA",
                        "produto": "Compra Avulsa",
                        "valor_total": val_compra,
                        "porcentagem": f"{p_val:g}%",
                        "diferenca": dif_str
                    }
                    salvar_transacao(item)
                    st.success("Compra registrada com sucesso!")
                    st.rerun()
                else:
                    st.error("Por favor, digite um valor válido para a compra.")

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
            val_desp = st.number_input("Valor (R$)", value=None, min_value=0.01, step=1.0, placeholder="0.00")
            
        sub_desp = st.form_submit_button("➕ Cadastrar Despesa", type="primary")
        if sub_desp:
            if desc_desp.strip() and val_desp is not None:
                salvar_despesa(dt_desp.strftime("%d/%m/%Y"), desc_desp, val_desp)
                st.success("Despesa cadastrada!")
                st.rerun()
            else:
                st.error("Informe uma descrição e um valor válido.")

    st.divider()
    
    st.subheader("Histórico de Despesas")
    
    conn = sqlite3.connect(DB_PATH)
    df_todas_desp = pd.read_sql_query("SELECT id, data, descricao, valor, data_registro FROM despesas", conn)
    conn.close()

    meses_dict_desp = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }

    if not df_todas_desp.empty:
        df_todas_desp["dt_parsed"] = pd.to_datetime(df_todas_desp["data"], format="%d/%m/%Y", errors="coerce")
        # Ordenação por data cadastrada (mais antigo em cima)
        df_todas_desp = df_todas_desp.sort_values(by="dt_parsed", ascending=True)

        anos_disponiveis_d = sorted(df_todas_desp["dt_parsed"].dt.year.dropna().astype(int).unique(), reverse=True)
        anos_opcoes_d = ["Todos os Anos"] + [str(a) for a in anos_disponiveis_d]

        col_fd1, col_fd2, col_fd3 = st.columns([1, 1, 1])
        with col_fd1:
            ano_sel_d = st.selectbox("Filtrar por Ano", anos_opcoes_d, key="sel_ano_desp")
        with col_fd2:
            mes_sel_d = st.selectbox("Filtrar por Mês", ["Todos os Meses"] + list(meses_dict_desp.values()), key="sel_mes_desp")
        with col_fd3:
            st.write("")
            st.write("")
            mostrar_tudo_desp = st.checkbox("Mostrar Histórico Completo", value=False, key="chk_tudo_desp")

        df_desp_filtrado = df_todas_desp.copy()

        if not mostrar_tudo_desp:
            if ano_sel_d != "Todos os Anos":
                df_desp_filtrado = df_desp_filtrado[df_desp_filtrado["dt_parsed"].dt.year == int(ano_sel_d)]
            if mes_sel_d != "Todos os Meses":
                m_num_d = [k for k, v in meses_dict_desp.items() if v == mes_sel_d][0]
                df_desp_filtrado = df_desp_filtrado[df_desp_filtrado["dt_parsed"].dt.month == m_num_d]

        df_exibir_desp = df_desp_filtrado.drop(columns=["dt_parsed"])

        if not df_exibir_desp.empty:
            st.dataframe(df_exibir_desp, use_container_width=True)
            tot_d_exibido = df_exibir_desp['valor'].sum()
            st.markdown(f"**Total Exibido em Despesas:** <span style='color: #c62828; font-size: 1.3em; font-weight: bold;'>R$ {tot_d_exibido:.2f}</span>", unsafe_allow_html=True)
        else:
            st.info("Nenhuma despesa encontrada para os filtros selecionados.")

        st.divider()
        st.subheader("🛠️ Editar ou Excluir Despesa")
        
        opcoes_despesa = {
            f"ID #{row['id']} - {row['data']} | {row['descricao']} (R$ {row['valor']:.2f})": row['id']
            for _, row in df_exibir_desp.iterrows()
        } if not df_exibir_desp.empty else {}

        if opcoes_despesa:
            item_selecionado = st.selectbox("Selecione uma despesa para alterar:", list(opcoes_despesa.keys()))
            id_selecionado = opcoes_despesa[item_selecionado]
            
            dados_item = df_todas_desp[df_todas_desp['id'] == id_selecionado].iloc[0]
            
            col_ed1, col_ed2, col_ed3 = st.columns([2, 1, 1])
            with col_ed1:
                novo_desc = st.text_input("Editar Descrição", value=dados_item['descricao'], key=f"desc_{id_selecionado}")
            with col_ed2:
                novo_valor = st.number_input("Editar Valor (R$)", value=float(dados_item['valor']), min_value=0.01, step=1.0, key=f"val_{id_selecionado}")
            with col_ed3:
                st.write("Ações:")
                btn_salvar_edit = st.button("💾 Salvar Alteração", key=f"btn_edit_{id_selecionado}")
                btn_deletar = st.button("🗑️ Deletar Despesa", type="primary", key=f"btn_del_{id_selecionado}")

            if btn_salvar_edit:
                atualizar_despesa(id_selecionado, novo_desc, novo_valor)
                st.success(f"Despesa #{id_selecionado} atualizada com sucesso!")
                st.rerun()

            if btn_deletar:
                modal_confirmar_deletar_despesa(id_selecionado, dados_item['descricao'])
    else:
        st.info("Nenhuma despesa cadastrada no sistema.")

# --- ABA 3: BALANÇO GERAL ---
with aba_balanco:
    st.header("📊 Balanço Geral de Lançamentos")
    
    conn = sqlite3.connect(DB_PATH)
    df_hist = pd.read_sql_query("SELECT id, data, tipo, produto, valor_total, porcentagem, diferenca, data_exportacao FROM historico", conn)
    df_desp_balanco = pd.read_sql_query("SELECT data, valor FROM despesas", conn)
    conn.close()

    if not df_hist.empty:
        df_hist["dt_parsed"] = pd.to_datetime(df_hist["data"], format="%d/%m/%Y", errors="coerce")
        df_desp_balanco["dt_parsed"] = pd.to_datetime(df_desp_balanco["data"], format="%d/%m/%Y", errors="coerce")

        # Ordenação REAL pela data cadastrada (coluna 'data' da esquerda)
        # Mais antigo no topo, mais recente embaixo (utilizando 'id' como desempate)
        df_hist = df_hist.sort_values(by=["dt_parsed", "id"], ascending=[True, True])

        anos_disponiveis = sorted(df_hist["dt_parsed"].dt.year.dropna().astype(int).unique(), reverse=True)
        anos_opcoes = ["Todos os Anos"] + [str(a) for a in anos_disponiveis]

        meses_nomes_dict = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            ano_sel_b = st.selectbox("Filtrar por Ano", anos_opcoes, key="sel_ano_balanco")
        with col_f2:
            mes_sel_b = st.selectbox("Filtrar por Mês", ["Todos os Meses"] + list(meses_nomes_dict.values()), key="sel_mes_balanco")
        with col_f3:
            tipo_filtro = st.selectbox("Filtrar por Tipo", ["TODOS", "VENDA", "COMPRA"], key="sel_tipo_balanco")

        df_hist_filtrado = df_hist.copy()
        df_desp_filtrado = df_desp_balanco.copy()

        if ano_sel_b != "Todos os Anos":
            ano_num = int(ano_sel_b)
            df_hist_filtrado = df_hist_filtrado[df_hist_filtrado["dt_parsed"].dt.year == ano_num]
            df_desp_filtrado = df_desp_filtrado[df_desp_filtrado["dt_parsed"].dt.year == ano_num]

        if mes_sel_b != "Todos os Meses":
            mes_num = [k for k, v in meses_nomes_dict.items() if v == mes_sel_b][0]
            df_hist_filtrado = df_hist_filtrado[df_hist_filtrado["dt_parsed"].dt.month == mes_num]
            df_desp_filtrado = df_desp_filtrado[df_desp_filtrado["dt_parsed"].dt.month == mes_num]

        df_exibir = df_hist_filtrado.copy()
        if tipo_filtro != "TODOS":
            df_exibir = df_exibir[df_exibir["tipo"] == tipo_filtro]

        df_exibir_display = df_exibir.drop(columns=["dt_parsed"])

        # Função para destacar com cores as linhas da tabela
        def estilar_linhas(row):
            if row["tipo"] == "VENDA":
                return ['background-color: #d4edda; color: #155724; font-weight: bold;'] * len(row)
            elif row["tipo"] == "COMPRA":
                return ['background-color: #f8d7da; color: #721c24; font-weight: bold;'] * len(row)
            return [''] * len(row)

        st.dataframe(df_exibir_display.style.apply(estilar_linhas, axis=1), use_container_width=True)

        tot_vendas = df_hist_filtrado[df_hist_filtrado["tipo"] == "VENDA"]["valor_total"].sum()
        tot_compras = df_hist_filtrado[df_hist_filtrado["tipo"] == "COMPRA"]["valor_total"].sum()
        tot_despesas = df_desp_filtrado["valor"].sum() if not df_desp_filtrado.empty else 0.0
        lucro_bruto = tot_vendas - tot_compras

        soma_porcentagem_tot = 0.0
        soma_diferenca_tot = 0.0

        for _, row in df_hist_filtrado.iterrows():
            p_str = str(row["porcentagem"]).replace("%", "").strip()
            if p_str != "-":
                try:
                    soma_porcentagem_tot += float(p_str)
                except ValueError:
                    pass

            d_str = str(row["diferenca"]).strip()
            if d_str != "-":
                try:
                    soma_diferenca_tot += float(d_str)
                except ValueError:
                    pass

        saldo_estoque = obter_saldo_estoque()
        balanco_corrigido = saldo_estoque + tot_vendas - tot_compras - tot_despesas

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.markdown(f"**Total Vendas**<h3 style='color: #2e7d32; margin-top:0;'>R$ {tot_vendas:.2f}</h3>", unsafe_allow_html=True)
        c2.markdown(f"**Total Compras**<h3 style='color: #c62828; margin-top:0;'>R$ {tot_compras:.2f}</h3>", unsafe_allow_html=True)
        
        cor_lb = "#2e7d32" if lucro_bruto >= 0 else "#c62828"
        c3.markdown(f"**Lucro Bruto**<h3 style='color: {cor_lb}; margin-top:0;'>R$ {lucro_bruto:.2f}</h3>", unsafe_allow_html=True)
        c4.markdown(f"**📊 Soma Porcentagens**<h3 style='color: #1565c0; margin-top:0;'>{soma_porcentagem_tot:g}%</h3>", unsafe_allow_html=True)
        c5.markdown(f"**⚖️ Soma Diferenças**<h3 style='color: #ef6c00; margin-top:0;'>R$ {soma_diferenca_tot:.2f}</h3>", unsafe_allow_html=True)

        cor_bc = "#2e7d32" if balanco_corrigido >= 0 else "#c62828"
        st.markdown(
            f"### 📐 Balanço Corrigido (Caixa + Vendas - Compras - Despesas)\n"
            f"<h2 style='color: {cor_bc}; margin-top:0;'>R$ {balanco_corrigido:.2f}</h2>",
            unsafe_allow_html=True
        )

        st.divider()
        st.subheader("🛠️ Editar ou Excluir Lançamento")
        
        if not df_exibir.empty:
            opcoes_hist = {
                f"ID #{row['id']} - {row['data']} | [{row['tipo']}] R$ {row['valor_total']:.2f} (Perc: {row['porcentagem']})": row['id']
                for _, row in df_exibir.iterrows()
            }
            
            item_hist_sel = st.selectbox("Selecione um lançamento para alterar:", list(opcoes_hist.keys()), key="select_hist")
            id_hist_sel = opcoes_hist[item_hist_sel]
            
            dados_hist_item = df_hist[df_hist['id'] == id_hist_sel].iloc[0]
            
            try:
                dt_obj = datetime.strptime(dados_hist_item['data'], "%d/%m/%Y").date()
            except ValueError:
                dt_obj = datetime.now().date()

            col_h1, col_h2, col_h3, col_h4 = st.columns([1, 1, 1, 1])
            
            with col_h1:
                nova_dt_h = st.date_input("Nova Data", value=dt_obj, key=f"dt_h_{id_hist_sel}")
            
            with col_h2:
                novo_val_h = st.number_input("Novo Valor (R$)", value=float(dados_hist_item['valor_total']), min_value=0.01, step=1.0, key=f"val_h_{id_hist_sel}")
                
            with col_h3:
                is_compra = dados_hist_item['tipo'] == 'COMPRA'
                perc_atual_val = 0.0
                if is_compra:
                    p_raw = str(dados_hist_item['porcentagem']).replace('%', '').strip()
                    try:
                        perc_atual_val = float(p_raw)
                    except ValueError:
                        perc_atual_val = 0.0
                
                nova_perc_h = st.number_input("Porcentagem (%)", value=perc_atual_val, min_value=0.0, step=0.5, disabled=not is_compra, key=f"perc_h_{id_hist_sel}")

            with col_h4:
                st.write("Ações:")
                btn_salvar_hist = st.button("💾 Salvar Alteração", key=f"btn_save_h_{id_hist_sel}")
                btn_deletar_hist = st.button("🗑️ Deletar Lançamento", type="primary", key=f"btn_del_h_{id_hist_sel}")

            if btn_salvar_hist:
                dt_str_nova = nova_dt_h.strftime("%d/%m/%Y")
                if is_compra:
                    perc_str_nova = f"{nova_perc_h:g}%"
                    dif_nova = f"{(novo_val_h / nova_perc_h):.2f}" if nova_perc_h > 0 else "0.00"
                else:
                    perc_str_nova = "-"
                    dif_nova = "-"
                    
                atualizar_transacao(id_hist_sel, dt_str_nova, novo_val_h, perc_str_nova, dif_nova)
                st.success(f"Lançamento #{id_hist_sel} atualizado com sucesso!")
                st.rerun()

            if btn_deletar_hist:
                modal_confirmar_deletar_transacao(id_hist_sel, dados_hist_item['tipo'], float(dados_hist_item['valor_total']))
        else:
            st.info("Nenum lançamento encontrado para os filtros selecionados.")
            
    else:
        st.info("Nenhum lançamento encontrado.")

# --- ABA 4: ESTOQUE CAIXA ---
with aba_estoque:
    st.header("💵 Dinheiro em Estoque Caixa")
    
    saldo_atual = obter_saldo_estoque()
    st.markdown(f"**Saldo Atual em Estoque:** <h2 style='color: #1565c0; margin-top:0;'>R$ {saldo_atual:.2f}</h2>", unsafe_allow_html=True)
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        valor_alterar = st.number_input("Valor para Alterar (R$)", value=None, min_value=0.01, step=1.0, placeholder="Digite o valor...")
    
    with col_e2:
        st.write("Ações:")
        if st.button("➕ Aumentar Saldo", type="primary"):
            if valor_alterar is not None:
                atualizar_saldo_estoque(saldo_atual + valor_alterar)
                st.success("Saldo aumentado!")
                st.rerun()
            else:
                st.error("Informe um valor.")
        if st.button("➖ Diminuir Saldo"):
            if valor_alterar is not None:
                atualizar_saldo_estoque(saldo_atual - valor_alterar)
                st.success("Saldo diminuído!")
                st.rerun()
            else:
                st.error("Informe um valor.")

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
    ax.plot(meses_nomes, c_list, marker='o', color='#c62828', label='Compras (R$)')
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
                modal_confirmar_restauracao(uploaded_file)
