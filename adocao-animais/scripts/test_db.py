
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

try:
    with psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        sslmode=os.getenv("DB_SSLMODE", "require"),
        connect_timeout=10,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT current_database(), current_user, version()"
            )
            database, user, version = cur.fetchone()

            print("Conexão com o PostgreSQL estabelecida!")
            print(f"Banco: {database}")
            print(f"Usuário: {user}")
            print(f"PostgreSQL: {version.split(',')[0]}")

except Exception as exc:
    print(f"Falha na conexão: {type(exc).__name__}: {exc}")
