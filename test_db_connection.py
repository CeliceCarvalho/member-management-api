import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

urls = ["DATABASE_URL", "DIRECT_URL"]

for env_name in urls:
    url = os.getenv(env_name)

    if not url:
        print(f"{env_name} nao encontrada no .env")
        continue

    print(f"\nTestando {env_name}...")

    try:
        engine = create_engine(url, pool_pre_ping=True)

        with engine.connect() as conn:
            result = conn.execute(
                text("select current_database(), current_user, now()")
            ).first()

            print(f"{env_name} OK")
            print(f"Banco: {result[0]}")
            print(f"Usuario: {result[1]}")
            print(f"Data/Hora: {result[2]}")

    except Exception as error:
        print(f"Erro ao conectar com {env_name}")
        print(error)
