import streamlit as st
import psycopg2
import pandas as pd
import datetime

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

# cadastro de picklist
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
    st.subheader("✏️ Editar um Valor Existente")

    if not df.empty:
        # Escolher um valor para editar
        selected_id = st.selectbox("Selecione um valor para editar", df["id"].tolist(), format_func=lambda x: df[df["id"] == x]["valor"].values[0])
        new_edit_value = st.text_input("📝 Novo Texto para este Valor")

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

# Rodar a página
st.sidebar.title("📌 Menu")
pagina = st.sidebar.radio("Escolha uma opção:", ["Cadastrar Despesa", "Consultar Despesas", "Gerenciar Picklists"])

if pagina == "Cadastrar Despesa":
    cadastrar_despesa()
elif pagina == "Consultar Despesas":
    visualizar_despesas()
elif pagina == "Gerenciar Picklists":
    gerenciar_picklists()