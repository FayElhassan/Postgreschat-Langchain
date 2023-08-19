# tools/sql_database_toolkit.py

from langchain.sql_database import SQLDatabase
from sqlalchemy import create_engine
from config.settings import POSTGRESQL, PostgresConfig
# from sql_analyzer.log_init import logger  # Uncomment if you want to use the logger from sql_analyzer

def sql_db_factory() -> SQLDatabase:
    if POSTGRESQL:
        db = SQLDatabase.from_uri(f"postgresql+psycopg2://{PostgresConfig.user}:{PostgresConfig.password}@{PostgresConfig.host}:{PostgresConfig.port}/{PostgresConfig.database}")
        return db
    else:
        raise Exception(f"Could not create sql database factory.")
