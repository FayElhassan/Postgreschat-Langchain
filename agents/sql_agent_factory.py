# agents/sql_agent_factory.py

from langchain.agents import create_sql_agent, AgentExecutor
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferMemory

from langchain.agents.agent import AgentOutputParser
from langchain.agents.mrkl.prompt import FORMAT_INSTRUCTIONS
from tools.sql_database_toolkit import sql_db_factory
from tools.sql_tool import ExtendedSQLDatabaseToolkit
from config.settings import cfg


from typing import Tuple, Dict
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_sql_agent
from langchain.agents import AgentExecutor
from langchain.agents.agent_types import AgentType
from typing import Tuple, Dict
from langchain.memory import ConversationBufferMemory
from langchain.prompts.chat import MessagesPlaceholder
from langchain.agents.agent import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish, OutputParserException
from langchain.agents.mrkl.prompt import FORMAT_INSTRUCTIONS
from tools.sql_tool import DatabaseSchema
from typing import Union
import re
from config.settings import SQL_PREFIX, SQL_SUFFIX

from config.settings import cfg
#from sql_analyzer.log_init import logger
from tools.sql_tool import ExtendedSQLDatabaseToolkit
from tools.sql_database_toolkit import sql_db_factory
import logging

# Setting up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

FINAL_ANSWER_ACTION = "Final Answer:"


class ExtendedMRKLOutputParser(AgentOutputParser):
     def get_format_instructions(self) -> str:
        return FORMAT_INSTRUCTIONS

     def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        answer_type, content = self.includes_final_answer(text)
        
        if content:  # Ensure content is not None before proceeding with regex
            # Check if content matches a list-like pattern
            pattern = r"'?(.*?)'? - ([\d,]+)"
            matches = re.findall(pattern, content)
            if matches:
                structured_data = [{"description": desc.strip(), "value": val.replace(',', '').strip()} for desc, val in matches]
                formatted_output = pd.DataFrame(structured_data).to_string()  # Convert to tabular format
                return AgentFinish({"output": formatted_output}, text)

        # Existing parsing logic for actions
        regex = (
            r"Action\s*\d*\s*:[\s]*(.*?)[\s]*Action\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        )
        action_match = re.search(regex, text, re.DOTALL)
        if action_match:
            action = action_match.group(1).strip()
            action_input = action_match.group(2)
            tool_input = action_input.strip(" ")
            if not tool_input.startswith("SELECT "):
                tool_input = tool_input.strip('"')
            return AgentAction(action, tool_input, text)
        
        # If none of the patterns are recognized, just return the text as it is
        return AgentFinish({"output": text}, text)

     def includes_final_answer(self, text):
        # Check for any final answer pattern
        if FINAL_ANSWER_ACTION in text:
            return "answer", text.split(FINAL_ANSWER_ACTION)[-1].strip()
        
        return None, None

     @property
     def _type(self) -> str:
        return "mrkl"



def setup_memory() -> Tuple[Dict, ConversationBufferMemory]:
    agent_kwargs = {
        "extra_prompt_messages": [MessagesPlaceholder(variable_name="memory")],
    }
    memory = ConversationBufferMemory(memory_key="memory", return_messages=True)
    return agent_kwargs, memory
def init_sql_db_toolkit() -> ExtendedSQLDatabaseToolkit:
    db = sql_db_factory()
    db_schema = DatabaseSchema(db)  # Initialize your custom schema with the db
    toolkit = ExtendedSQLDatabaseToolkit(db=db, llm=cfg.llm, schema=db_schema)
    return toolkit

# def init_sql_db_toolkit() -> ExtendedSQLDatabaseToolkit:
#     db = sql_db_factory()
#     toolkit = ExtendedSQLDatabaseToolkit(db=db, llm=cfg.llm)
#     return toolkit

def agent_factory() -> AgentExecutor:
    try:
        sql_db_toolkit = init_sql_db_toolkit()
        db = sql_db_factory()

        # Initialize your custom schema
        db_schema = DatabaseSchema(db)

        # Pass the schema to the toolkit
        sql_db_toolkit = ExtendedSQLDatabaseToolkit(
            db=sql_db_toolkit.db,
            llm=sql_db_toolkit.llm,
            schema=db_schema,  # Pass the schema here
        )
        
        prompt = f"{SQL_PREFIX}\n{input}\n{SQL_SUFFIX}"
        
        agent_executor = create_sql_agent(
            llm=cfg.llm,
            toolkit=sql_db_toolkit,
            verbose=True,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            memory=setup_memory(),
            prompt=prompt  # Here, we pass the modified prompt
            
        )
        
        agent = agent_executor.agent
        agent.output_parser = ExtendedMRKLOutputParser()
        return agent_executor
        
    except Exception as e:
        error_message = str(e)
        if "no such table" in error_message:
            logger.error("The specified table doesn't exist in the database.")
        elif "no such column" in error_message:
            logger.error("The specified column doesn't exist in the table.")
        else:
            logger.error(f"Error while setting up the agent: {e}")
        raise



if __name__ == "__main__":
    try:
        agent_executor = agent_factory()
        result = agent_executor.run("Describe all tables")
    except Exception as e:
        logger.error(f"Error while executing the agent: {e}")
