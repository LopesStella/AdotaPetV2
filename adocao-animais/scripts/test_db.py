import os
import pg8000.native
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DB_HOST")
port = int(os.getenv("DB_PORT", 5432))
database = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

try:
    conn = pg8000.native.Connection(
        user=user,
        host=host,
        port=port,
        database=database,
        password=password,
        ssl_context=True
    )
    print("Conexão realizada com sucesso!")
    conn.close()
except Exception as e:
    print(f"Falha na conexão: {e}")