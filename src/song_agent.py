from collections.abc import AsyncIterable
from typing import Any
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_community.chat_models import ChatOCIGenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from modules.fuse_config import FuseConfig
from modules.oci_client import LLM_Client

oci_client = LLM_Client()
fuse_handler = FuseConfig()
id = fuse_handler.generate_id()
memory = MemorySaver()

@tool
def add_song(name:str)->str:
    """ Adds a song to user playlist """
    return f"{name} added to user playlist successfully"

class SongAgent:
    """ Song agent - expert in adding songs to playlist """

    SYSTEM_INSTRUCTION = (
        "You are an expert in manage the new songs for the user playlist"
        "You can use the add_song tool to complete queries about adding songs to playlist"
        "Do not attempt to answer not playlist related questions, politely indicate that you have no such capacity"
    )

    def __init__(self):
        self.model = oci_client.build_llm_client()
        # model_source = os.getenv('model_source', 'google')
        # if model_source == 'google':
        #     self.model = ChatGoogleGenerativeAI(model='gemini-2.0-flash')
        self.tools = [add_song]
        self.song_agent = create_react_agent(
            model=self.model,
            tools=self.tools,
            checkpointer=memory,
            prompt=self.SYSTEM_INSTRUCTION
        )

    async def stream(self,query,context_id)-> AsyncIterable[dict[str,Any]]:
        inputs = {'messages': [('user', query)]}
        config = {'configurable': {'thread_id': context_id},'callbacks':[fuse_handler.get_handler()],'metadata':{'langfuse_session_id':id}}
        final_response = []
        # Solve the AI Message msgpack error with try instead of library change
        try:
            for chunk in self.song_agent.stream(inputs,config,stream_mode="values"):
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