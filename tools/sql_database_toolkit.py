
# tools/sql_database_toolkit.py

from langchain.sql_database import SQLDatabase
from config.settings import POSTGRESQL, PostgresConfig

def sql_db_factory() -> SQLDatabase:
    if POSTGRESQL:
        db_uri = (
            f"postgresql+psycopg2://"
            f"{PostgresConfig.user}:"
            f"{PostgresConfig.password}@"
            f"{PostgresConfig.host}:"
            f"{PostgresConfig.port}/"
            f"{PostgresConfig.database}"
        )
        db = SQLDatabase.from_uri(db_uri)
        return db
    else:
        raise Exception(f"POSTGRESQL setting was set to False or not provided.")
