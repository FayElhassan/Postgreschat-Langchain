import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
#from sql_analyzer.log_init import logger  # Uncomment this if you want to use the logger from sql_analyzer

load_dotenv()

POSTGRESQL = "postgresql"
SELECTED_DBS = [POSTGRESQL]


class PostgresConfig:
    user = os.getenv("POSTGRES_USER", "Abdalla")
    password = os.getenv("POSTGRES_PASSWORD", "Admin1234")
    host = os.getenv("POSTGRES_HOST", "database-1.ccpah0etv9im.eu-north-1.rds.amazonaws.com")
    database = os.getenv("POSTGRES_DATABASE", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")


class Config:
    model = "gpt-3.5-turbo-16k-0613"  # You can adjust the model name as per your requirements
    llm = ChatOpenAI(model=model, temperature=0, openai_api_key="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")
    
    db_connection_string = os.getenv("DB_CONNECTION_STRING", 
                                     f"postgresql+psycopg2://{PostgresConfig.user}:{PostgresConfig.password}@{PostgresConfig.host}:{PostgresConfig.port}/{PostgresConfig.database}")
    
    postgres_config = PostgresConfig()
    selected_db = os.getenv("SELECTED_DB", POSTGRESQL)
    
    if selected_db not in SELECTED_DBS:
        raise Exception(
            f"Selected DB {selected_db} not recognized. The possible values are: {SELECTED_DBS}."
        )


cfg = Config()

#if __name__ == "__main__":
    # logger.info("LLM %s", cfg.llm)  # Uncomment this if you want to use the logger from sql_analyzer
    # logger.info("db_uri %s", cfg.db_connection_string)  # Uncomment this if you want to use the logger from sql_analyzer
    # logger.info("selected_db %s", cfg.selected_db)  # Uncomment this if you want to use the logger from sql_analyzer
