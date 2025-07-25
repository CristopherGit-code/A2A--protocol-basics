from collections.abc import AsyncIterable
from typing import Any
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from modules.fuse_config import FuseConfig
from modules.oci_client import LLM_Client

oci_client = LLM_Client()
fuse_handler = FuseConfig()
id = fuse_handler.generate_id()
memory = MemorySaver()

@tool
def find_word(word:str)->str:
    """ Looks for  unknown word definition"""
    return "No other words found"

class ArtAgent:
    """ Art agent - expert in creating poems about a given topic """

    SYSTEM_INSTRUCTION = (
        "You are an expert in writting poems about a given topic from the user"
        "Call a tool only when needed, if the query could be answered without a tool, anwer. PRIORITY is getting the user a good resposne to query"
        "Always answer in poem structure, use literal resources."
        "Always anser in less than 200 words"
    )

    def __init__(self):
        self.model = oci_client.build_llm_client()
        self.tools = [find_word]
        self.art_agent = create_react_agent(
            model=self.model,
            tools=self.tools,
            checkpointer=memory,
            prompt=self.SYSTEM_INSTRUCTION
        )

    async def stream(self,query,context_id)-> AsyncIterable[dict[str,Any]]:
        inputs = {'messages': [('user', query)]}
        config = {'configurable': {'thread_id': context_id},'callbacks':[fuse_handler.get_handler()],'metadata':{'langfuse_session_id':id}}
        final_response = []
        try:
            for chunk in self.art_agent.stream(inputs,config,stream_mode="values"):
                message = chunk['messages'][-1]
                final_response.append(message.content)
                if isinstance(message,AIMessage):
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': f'Calling agent: {message.content}',
                    }
                elif isinstance(message,ToolMessage):
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': f'Tool call: {message.content}',
                    }
        except Exception as e:
            final_response.append(e)
            final_response.append("error")
            yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': 'error',
                }
            
        if final_response[-1] == "error":
            yield {
                'is_task_complete': False,
                'require_user_input': True,
                'content': final_response[-2],
            }
        else:
            yield {
                'is_task_complete': True,
                'require_user_input': False,
                'content': final_response[-1],
            }
    
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']