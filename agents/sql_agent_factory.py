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
        includes_answer = self.includes_final_answer(text)
        regex = (
            r"Action\s*\d*\s*:[\s]*(.*?)[\s]*Action\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        )
        action_match = re.search(regex, text, re.DOTALL)
        if action_match:
            if includes_answer:
                raise OutputParserException(
                    "Parsing LLM output produced both a final answer "
                    f"and a parse-able action: {text}"
                )
            action = action_match.group(1).strip()
            action_input = action_match.group(2)
            tool_input = action_input.strip(" ")
            # ensure if it's a well-formed SQL query we don't remove any trailing " chars
            if not tool_input.startswith("SELECT "):
                tool_input = tool_input.strip('"')

            return AgentAction(action, tool_input, text)
        elif includes_answer:
            return AgentFinish(
                {"output": text.split(FINAL_ANSWER_ACTION)[-1].strip()}, text
            )
        # Handle the specific scenario where the LLM returns "Action: None"
        elif "Action: None" in text:
            return AgentFinish({"output": "I couldn't determine an appropriate action based on the input."}, text)
        elif not re.search(r"Action\s*\d*\s*:[\s]*(.*?)", text, re.DOTALL):
            raise OutputParserException(
                f"Could not parse LLM output: `{text}`",
                observation="Invalid Format: Missing 'Action:' after 'Thought:'",
                llm_output=text,
                send_to_llm=True,
            )
        elif not re.search(
            r"[\s]*Action\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)", text, re.DOTALL
        ):
            raise OutputParserException(
                f"Could not parse LLM output: `{text}`",
                observation="Invalid Format:"
                " Missing 'Action Input:' after 'Action:'",
                llm_output=text,
                send_to_llm=True,
            )
        else:
            raise OutputParserException(f"Could not parse LLM output: `{text}`")



    def includes_final_answer(self, text):
        includes_answer = (
            FINAL_ANSWER_ACTION in text or FINAL_ANSWER_ACTION.lower() in text.lower()
        )
        return includes_answer

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
    toolkit = ExtendedSQLDatabaseToolkit(db=db, llm=cfg.llm)
    return toolkit

def agent_factory() -> AgentExecutor:
    try:
        sql_db_toolkit = init_sql_db_toolkit()

        # Initialize your custom schema
        db_schema = DatabaseSchema()

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
