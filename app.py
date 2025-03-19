import streamlit as st
import psycopg2
import pandas as pd
import datetime
import matplotlib.pyplot as plt

# Configuração do banco de dados
DATABASE_URL = "postgresql://postgres:BfhczSllCYbrWIFedpqbkCxEmxwpwBsO@turntable.proxy.rlwy.net:10200/railway"  # Substitua pela sua URL do Railway

def get_connection():
    return psycopg2.connect(DATABASE_URL)

@st.cache_data
def get_picklist_options(nome):
    """Busca os valores dos picklists no banco e armazena em cache para evitar recarregamento excessivo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM picklists WHERE nome = %s", (nome,))
    options = [row[0] for row in cursor.fetchall()]
    conn.close()
    return options

# Página para cadastrar despesas
def cadastrar_despesa():
    st.title("📌 Cadastrar Nova Despesa")

    # Campos do formulário
    data = st.date_input("📅 Data da Despesa", format="DD/MM/YYYY")
    data_formatada = data.strftime("%d/%m/%Y")  # Converte para o formato correto para exibição
    st.write(f"🗓️ Data Selecionada: {data_formatada}")  # Mostra a data formatada corretamente
    
    detalhamento = st.text_area("📝 Detalhamento")
    categoria = st.selectbox("📂 Categoria", get_picklist_options("Categoria"))
    tipo = st.selectbox("📊 Tipo", get_picklist_options("Tipo"))
    valor = st.number_input("💰 Valor Unitário (R$)", min_value=0.0, format="%.2f")
    quem = st.selectbox("🙋‍♂️ Quem", get_picklist_options("Quem"))
    recorrente = st.selectbox("🔄 Recorrente", get_picklist_options("Recorrente"))
    forma = st.selectbox("💳 Forma de Pagamento", get_picklist_options("Forma"))

    # Botão de salvar
    if st.button("💾 Salvar Despesa"):
        conn = get_connection()
        cursor = conn.cursor()
        
        # Converter data formatada para o formato correto antes de inserir no banco
        data_sql = datetime.datetime.strptime(data_formatada, "%d/%m/%Y").date()
        
        cursor.execute('''
            INSERT INTO despesas (data, detalhamento, categoria, tipo, valor, quem, recorrente, forma)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (data_sql, detalhamento, categoria, tipo, valor, quem, recorrente, forma))
        
        conn.commit()
        conn.close()
        st.success("✅ Despesa cadastrada com sucesso!")

def gerenciar_despesas():
    st.title("📝 Gerenciar Despesas")

    conn = get_connection()
    query = "SELECT id, data, detalhamento, categoria, tipo, valor, quem, recorrente, forma FROM despesas ORDER BY data DESC"
    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        st.warning("⚠️ Nenhuma despesa cadastrada.")
        return

    # Exibir tabela de despesas
    st.dataframe(df)

    # Selecionar uma despesa para editar ou remover
    despesa_id = st.selectbox("📌 Selecione uma Despesa para Editar ou Remover", df["id"].tolist(), format_func=lambda x: f"{df[df['id'] == x]['detalhamento'].values[0]} - R$ {df[df['id'] == x]['valor'].values[0]:.2f}")

    if despesa_id:
        # Pegar os detalhes da despesa selecionada
        despesa = df[df["id"] == despesa_id].iloc[0]

        # Criar campos editáveis com os valores atuais da despesa
        data = st.date_input("📅 Data", pd.to_datetime(despesa["data"]).date(), format="DD/MM/YYYY")
        detalhamento = st.text_area("📝 Detalhamento", despesa["detalhamento"])
        categoria = st.selectbox("📂 Categoria", get_picklist_options("Categoria"), index=get_picklist_options("Categoria").index(despesa["categoria"]))
        tipo = st.selectbox("📊 Tipo", get_picklist_options("Tipo"), index=get_picklist_options("Tipo").index(despesa["tipo"]))
        valor = st.number_input("💰 Valor Unitário (R$)", min_value=0.0, value=float(despesa["valor"]), format="%.2f")
        quem = st.selectbox("🙋‍♂️ Quem", get_picklist_options("Quem"), index=get_picklist_options("Quem").index(despesa["quem"]))
        recorrente = st.selectbox("🔄 Recorrente", get_picklist_options("Recorrente"), index=get_picklist_options("Recorrente").index(despesa["recorrente"]))
        forma = st.selectbox("💳 Forma de Pagamento", get_picklist_options("Forma"), index=get_picklist_options("Forma").index(despesa["forma"]))

        # Criar colunas para botões de ação
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✏️ Atualizar Despesa"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE despesas SET data = %s, detalhamento = %s, categoria = %s, tipo = %s, valor = %s, quem = %s, recorrente = %s, forma = %s WHERE id = %s
                ''', (data, detalhamento, categoria, tipo, valor, quem, recorrente, forma, despesa_id))
                conn.commit()
                conn.close()
                st.success("✅ Despesa atualizada com sucesso!")
                st.rerun()

        with col2:
            if st.button("❌ Remover Despesa", key="delete"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM despesas WHERE id = %s", (despesa_id,))
                conn.commit()
                conn.close()
                st.success("🚮 Despesa removida com sucesso!")
                st.rerun()


# consulta despesas no banco e as exibe
def visualizar_despesas():
    st.title("📊 Consultar e Filtrar Despesas")

    conn = get_connection()
    query = "SELECT * FROM despesas ORDER BY data DESC"
    df = pd.read_sql(query, conn)
    conn.close()

    # Ajustar o formato da data para dd/mm/aaaa
    df["data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y")

    # Criar filtros
    st.subheader("🔍 Filtros")
    
    filtro_data = st.date_input("📅 Filtrar por Data", format="DD/MM/YYYY")
    filtro_categoria = st.selectbox("📂 Filtrar por Categoria", [""] + get_picklist_options("Categoria"))
    filtro_tipo = st.selectbox("📊 Filtrar por Tipo", [""] + get_picklist_options("Tipo"))
    filtro_quem = st.selectbox("🙋‍♂️ Filtrar por Quem", [""] + get_picklist_options("Quem"))
    filtro_forma = st.selectbox("💳 Filtrar por Forma de Pagamento", [""] + get_picklist_options("Forma"))

    # Aplicar filtros na DataFrame
    if filtro_data:
        df = df[df["data"] == filtro_data.strftime("%d/%m/%Y")]
    if filtro_categoria:
        df = df[df["categoria"] == filtro_categoria]
    if filtro_tipo:
        df = df[df["tipo"] == filtro_tipo]
    if filtro_quem:
        df = df[df["quem"] == filtro_quem]
    if filtro_forma:
        df = df[df["forma"] == filtro_forma]

    # Exibir a tabela com as despesas filtradas
    st.subheader("📋 Despesas Registradas")
    st.dataframe(df)

# picklist
def gerenciar_picklists():
    st.title("📌 Gerenciar Picklists")

    # Escolher qual picklist editar
    picklist_name = st.selectbox("📂 Escolha um Picklist para gerenciar", 
                                 ["Categoria", "Tipo", "Quem", "Recorrente", "Forma"])

    # Mostrar os valores já cadastrados
    st.subheader(f"Valores Atuais para {picklist_name}")
    conn = get_connection()
    df = pd.read_sql("SELECT id, valor FROM picklists WHERE nome = %s", conn, params=(picklist_name,))
    conn.close()
    st.dataframe(df)

    # Adicionar um novo valor
    new_value = st.text_input("✏️ Novo Valor para o Picklist")

    if st.button("➕ Adicionar Valor"):
        if new_value:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO picklists (nome, valor) VALUES (%s, %s)", (picklist_name, new_value))
            conn.commit()
            conn.close()
            st.success(f"✅ '{new_value}' adicionado ao picklist {picklist_name}")
            st.rerun()
        else:
            st.warning("⚠️ O campo de valor não pode estar vazio!")

    # Seção para editar valores existentes
    st.subheader("✏️ Editar ou Remover um Valor")

    if not df.empty:
        # Escolher um valor para editar ou excluir
        selected_id = st.selectbox("Selecione um valor", df["id"].tolist(), format_func=lambda x: df[df["id"] == x]["valor"].values[0])
        new_edit_value = st.text_input("📝 Novo Texto para este Valor")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✏️ Atualizar Valor"):
                if new_edit_value:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE picklists SET valor = %s WHERE id = %s", (new_edit_value, selected_id))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Valor atualizado para '{new_edit_value}'")
                    st.rerun()
                else:
                    st.warning("⚠️ O campo de novo valor não pode estar vazio!")

        with col2:
            if st.button("❌ Excluir Valor", key="delete"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM picklists WHERE id = %s", (selected_id,))
                conn.commit()
                conn.close()
                st.success(f"🚮 Valor removido com sucesso!")
                st.rerun()

    st.cache_data.clear()
    st.rerun()

def importar_despesas():
    st.title("📂 Importar Despesas do Google Sheets")

    # Upload do arquivo
    uploaded_file = st.file_uploader("📤 Faça upload do arquivo CSV exportado do Google Sheets", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, delimiter=",")  # Garante que está lendo corretamente

        st.write("🔍 Pré-visualização dos dados:")
        st.dataframe(df)

        # Validar se as colunas obrigatórias existem
        colunas_esperadas = ["data", "detalhamento", "categoria", "tipo", "valor", "quem", "recorrente", "forma"]
        if not all(col in df.columns for col in colunas_esperadas):
            st.error(f"⚠️ O arquivo deve conter as colunas: {', '.join(colunas_esperadas)}")
            return

        # Converter a coluna de data para o formato correto
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y").dt.strftime("%Y-%m-%d")

        # 🔥 Converter valores numéricos (substituir vírgulas por pontos)
        df["valor"] = df["valor"].astype(str).str.replace(",", ".")  # Substitui vírgula por ponto
        df["valor"] = df["valor"].astype(float)  # Converte para número

        # Inserir os dados no banco
        conn = get_connection()
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO despesas (data, detalhamento, categoria, tipo, valor, quem, recorrente, forma)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (row["data"], row["detalhamento"], row["categoria"], row["tipo"], row["valor"], row["quem"], row["recorrente"], row["forma"]))
        
        conn.commit()
        conn.close()

        st.success("✅ Despesas importadas com sucesso!")

def visualizar_consolidado():
    st.title("📊 Visão Consolidada das Despesas")

    conn = get_connection()
    query = """
        SELECT 
            EXTRACT(YEAR FROM data) AS ano,
            TO_CHAR(data, 'YYYY-MM') AS mes,
            quem, 
            tipo, 
            categoria, 
            SUM(valor) AS total
        FROM despesas
        GROUP BY ano, mes, quem, tipo, categoria
        ORDER BY ano DESC, mes DESC, quem, tipo, categoria;
    """
    df = pd.read_sql(query, conn)
    conn.close()

    # Ajustar formatos de data
    df["mes"] = pd.to_datetime(df["mes"]).dt.strftime("%m/%Y")
    
    # Criar um filtro por ano
    anos_disponiveis = df["ano"].unique().astype(int)
    ano_selecionado = st.selectbox("📅 Selecione o Ano", sorted(anos_disponiveis, reverse=True))

    # Filtrar os dados conforme o ano selecionado
    df_filtrado = df[df["ano"] == ano_selecionado]

    # Exibir tabela consolidada com opção de download
    st.subheader(f"📋 Dados Consolidados - {ano_selecionado}")
    st.dataframe(df_filtrado)

    # Criar botão para download
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Baixar CSV", csv, f"despesas_{ano_selecionado}.csv", "text/csv")

    # Criar visão hierárquica
    st.subheader(f"📊 Totais por Mês, Quem, Tipo e Categoria - {ano_selecionado}")
    grouped_df = df_filtrado.groupby(["mes", "quem", "tipo", "categoria"])["total"].sum().reset_index()

    for mes in grouped_df["mes"].unique():
        st.markdown(f"### 📅 {mes}")

        df_mes = grouped_df[grouped_df["mes"] == mes]
        for quem in df_mes["quem"].unique():
            st.markdown(f"#### 🙋‍♂️ {quem}")

            df_quem = df_mes[df_mes["quem"] == quem]
            for tipo in df_quem["tipo"].unique():
                st.markdown(f"##### 📊 {tipo}")

                df_tipo = df_quem[df_quem["tipo"] == tipo]
                for _, row in df_tipo.iterrows():
                    st.write(f"- **{row['categoria']}**: R$ {row['total']:.2f}")

    # Criar um gráfico comparativo por mês
    st.subheader("📊 Comparação de Gastos por Mês")

    grafico_df = df_filtrado.groupby(["mes"])["total"].sum().reset_index()
    plt.figure(figsize=(10, 5))
    plt.bar(grafico_df["mes"], grafico_df["total"], color="royalblue")
    plt.xlabel("Mês")
    plt.ylabel("Total Gasto (R$)")
    plt.title(f"Total de Gastos por Mês - {ano_selecionado}")
    plt.xticks(rotation=45)
    st.pyplot(plt)

# Rodar a página
st.sidebar.title("📌 Menu")
pagina = st.sidebar.radio("Escolha uma opção:", ["Cadastrar Despesa", "Consultar Despesas", "Gerenciar Despesas", "Gerenciar Picklists", "Importar Despesas", "Visão Consolidada"])

if pagina == "Cadastrar Despesa":
    cadastrar_despesa()
elif pagina == "Consultar Despesas":
    visualizar_despesas()
elif pagina == "Gerenciar Despesas":
    gerenciar_despesas()
elif pagina == "Gerenciar Picklists":
    gerenciar_picklists()
elif pagina == "Importar Despesas":
    importar_despesas()
elif pagina == "Visão Consolidada":
    visualizar_consolidado()
