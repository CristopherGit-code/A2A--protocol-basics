from collections.abc import AsyncIterable
from typing import Any
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from modules.fuse_config import FuseConfig
from modules.oci_client import LLM_Client
import logging, httpx
from uuid import uuid4
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
)

oci_client = LLM_Client()
fuse_handler = FuseConfig()
id = fuse_handler.generate_id()
memory = MemorySaver()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) 

class RemoteConnections():

    def __init__(self):
        self.servers:dict[str,A2AClient] = {}
        self.timeout = 30.0
        self.ports = [9999,8888]
    
    async def connect_server(self,base_url):
        async with httpx.AsyncClient() as httpx_client:
            resolver = A2ACardResolver(httpx_client,base_url)
            final_agent_card_use: AgentCard | None = None

            try:
                _public_card = await resolver.get_agent_card()
                final_agent_card_use = _public_card
                logger.info('\nUsing PUBLIC agent card for client initialization (default).')
            except Exception as e:
                logger.error(f'Critical error fetching public agent card: {e}', exc_info=True)
                raise RuntimeError('Failed to fetch the public agent card. Cannot continue.') from e
            
            client = A2AClient(httpx_client,final_agent_card_use)
            name = str(final_agent_card_use.name)
            logger.info(f'A2AClient initialized: {name}')

            return name, client

    async def start_servers(self):
        host = 'localhost'
        for port in self.ports:
            url=f"http://{host}:{port}/"
            name, client = await self.connect_server(url)
            self.servers[name] = client

    async def send_message_agent(self, agent_name:str, user_input:str)-> Any:
        client = self.servers[agent_name]
        send_message_payload: dict[str, Any] = {
                'message': {
                    'role': 'user',
                    'parts': [
                        {'kind': 'text', 'text': user_input}
                    ],
                    'message_id': uuid4().hex,
                },
            }
        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )
        response = await client.send_message(request, http_kwargs={"timeout": self.timeout})
        final_text = response.model_dump(mode='json', exclude_none=True)
        return final_text

@tool
def list_remote_agents():
    """List the available remote agents you can use to delegate the task."""
    return []
    if not remote_agent_connections:
        return []

    remote_agent_info = []
    for card in cards.values():
        remote_agent_info.append(
            {'name': card.name, 'description': card.description}
        )
    return remote_agent_info

@tool
def send_message():
    """ Sends message to an specific agent to complete the query requested """
    response = "hello"
    return response

class HostAgent:
    """ Host Agent to manage the connections to all the servers """

    SYSTEM_INSTRUCTION = (
        """You are an expert delegator that can delegate the user request to the
            appropriate remote agents.

            Discovery:
            - You can use `list_remote_agents` to list the available remote agents you
            can use to delegate the task.

            Execution:
            - For actionable requests, you can use `send_message` to interact with remote agents to take action.

            Be sure to include the remote agent name when you respond to the user.

            Please rely on tools to address the request, and don't make up the response. If you are not sure, please ask the user for more details.
            Focus on the most recent parts of the conversation primarily.
        """
    )

    def __init__(self):
        self.model = oci_client.build_llm_client()
        self.tools = [list_remote_agents,send_message]
        self.host_agent = create_react_agent(
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
            for chunk in self.host_agent.stream(inputs,config,stream_mode="values"):
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

async def main():
    remote_connection = RemoteConnections()
    await remote_connection.start_servers()
    print("Servers connected")
    response = await remote_connection.send_message_agent("Art agent","Who was nikola tesla?")
    print(response)
    response = await remote_connection.send_message_agent("Science agent","Who was nikola tesla?")
    print(response)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())