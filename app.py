# Adicione esta nova aba na lista de abas do seu app:
# aba_lancamentos, aba_despesas, aba_balanco, aba_estoque, aba_resumo, aba_backup = st.tabs(...)

with aba_backup:
    st.header("💾 Backup e Restauração do Banco de Dados")
    st.write("Como o Streamlit Cloud pode reiniciar o servidor, faça o download do seu banco de dados regularmente para manter uma cópia de segurança no seu computador.")
    
    col_b1, col_b2 = st.columns(2)
    
    # --- DOWNLOAD DO BACKUP ---
    with col_b1:
        st.subheader("📥 Baixar Cópia de Segurança")
        try:
            with open(DB_PATH, "rb") as file:
                btn_download = st.download_button(
                    label="Fazer Download do Banco de Dados (.db)",
                    data=file,
                    file_name=f"backup_mercadinho_{datetime.now().strftime('%Y_%m_%d')}.db",
                    mime="application/x-sqlite3",
                    type="primary"
                )
            st.caption("Salve este arquivo no seu computador para garantir a segurança dos seus lançamentos.")
        except FileNotFoundError:
            st.error("Arquivo de banco de dados ainda não foi criado.")

    # --- RESTAURAÇÃO DO BACKUP ---
    with col_b2:
        st.subheader("📤 Restaurar Banco de Dados")
        uploaded_file = st.file_uploader("Envie um arquivo .db de backup antigo", type=["db"])
        
        if uploaded_file is not None:
            if st.button("⚠️ Confirmar Restauração", type="primary"):
                # Sobrescreve o arquivo .db atual com o arquivo enviado
                with open(DB_PATH, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Banco de dados restaurado com sucesso! Recarregando a página...")
                st.rerun()
