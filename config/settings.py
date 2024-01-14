
# SQL_PREFIX and SQL_SUFFIX for structuring the prompt for the OpenAI agent
# SQL_PREFIX = """
# You are an agent designed to interact with a SQL database. Given an input question, create a syntactically correct {dialect} query. 
# - If a table or column name contains spaces, wrap it in double quotes. For example: "SELECT * FROM \"Sales orders\" WHERE \"Order ID\" = 5".
# - Always limit your query to at most {top_k} results using the LIMIT clause.
# - Order the results by a relevant column to return the most interesting examples.
# - Never query for all columns from a table. Ask only for the relevant columns given the question.
# - If you encounter a "no such table" error, rewrite your query by placing the table in quotes.
# - Avoid using a column name that doesn't exist in the table.
# - You have tools to interact with the database. Use only the specified tools and rely solely on the information they provide to construct your answer.
# - Double-check your query before executing. If you get an error, rewrite your query and try again. Do not attempt more than three times.
# - Do not execute any DML statements (INSERT, UPDATE, DELETE, DROP, etc.).
# - If the question seems unrelated to the database, simply reply with "I don't know".
# - If unable to determine an answer, provide the best possible response after a maximum of three attempts.
# """

# SQL_SUFFIX = "Begin!"

# Question: {input}
# thought = "I should look at the tables in the database to see what I can query."
# #some_string = f"The value is: {agent_scratchpad}"
SQL_PREFIX = """You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
Always limit your query to at most {top_k} results using the LIMIT clause.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for a the few relevant columns given the question.
If you get a "no such table" error, rewrite your query by using the table in quotes.
DO NOT use a column name that does not exist in the table.
You have access to tools for interacting with the database.
Only use the below tools. Only use the information returned by the below tools to construct your final answer.
You MUST double check your query before executing it. If you get an error while executing a query, rewrite a different query and try again.
DO NOT try to execute the query more than three times.
DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
If the question does not seem related to the database, just return "I don't know" as the answer.
If you cannot find a way to answer the question, just return the best answer you can find after trying at least three times.""";

SQL_SUFFIX = "Begin!"
Question: {input}
thought = "I should look at the tables in the database to see what I can query."
import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
#from agents.sql_agent_factory import ExtendedMRKLOutputParser
load_dotenv()

POSTGRESQL = "postgresql"
SELECTED_DBS = [POSTGRESQL]


class PostgresConfig:
    user = os.getenv("POSTGRES_USER", "____")
    password = os.getenv("POSTGRES_PASSWORD", "_____")
    host = os.getenv("POSTGRES_HOST", "------")
    database = os.getenv("POSTGRES_DATABASE", "_____")
    port = os.getenv("POSTGRES_PORT", "5432")

class Config:
    model = "gpt-3.5-turbo-16k-0613"  # You can adjust the model name as per your requirements
    llm = ChatOpenAI(model=model, temperature=0, openai_api_key="_________")
    db_connection_string = (
        f"postgresql+psycopg2://"
        f"{PostgresConfig.user}:"
        f"{PostgresConfig.password}@"
        f"{PostgresConfig.host}:"
        f"{PostgresConfig.port}/"
        f"{PostgresConfig.database}"
    )
    postgres_config = PostgresConfig()
    selected_db = os.getenv("SELECTED_DB", POSTGRESQL)
    #output_parser = ExtendedMRKLOutputParser()
    

cfg = Config()
