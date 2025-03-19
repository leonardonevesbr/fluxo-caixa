import psycopg2

# Substitua pela sua URL do Railway
DATABASE_URL = "postgresql://postgres:BfhczSllCYbrWIFedpqbkCxEmxwpwBsO@turntable.proxy.rlwy.net:10200/railway"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT 'Conexão bem-sucedida!'")
    print(cursor.fetchone()[0])
    conn.close()
except Exception as e:
    print("Erro ao conectar:", e)
