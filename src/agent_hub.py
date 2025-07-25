import asyncio
import base64
import json
import os
import uuid
import httpx
from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard,
    DataPart,
    Message,
    MessageSendConfiguration,
    MessageSendParams,
    Part,
    Task,
    TaskState,
    TextPart,
)
from remote_agent_connection import RemoteAgentConnections, TaskUpdateCallback
from modules.oci_client import LLM_Client
from collections.abc import AsyncIterable
from typing import Any
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from modules.oci_client import LLM_Client

class HostAgentHub:

    SYSTEM_INSTRUCTION = (
        "You are an expert in writting poems about a given topic from the user"
        "Call a tool only when needed, if the query could be answered without a tool, anwer. PRIORITY is getting the user a good resposne to query"
        "Always answer in poem structure, use literal resources."
        "Always anser in less than 200 words"
    )

    def __init__(self, remote_agent_addesses:list[str], http_client:httpx.AsyncClient):
        self.httpx_client = http_client
        self.remote_agent_connections:dict[str,RemoteAgentConnections] = {}
        self.cards:dict[str,AgentCard] = {}
        self.agents:str = ''
        self.oci_client = LLM_Client()
        self.model = self.oci_client.build_llm_client()
        self.memory = MemorySaver()
        loop = asyncio.get_running_loop()
        loop.create_task(self.init_remote_agent_addresses(remote_agent_addesses))

    async def init_remote_agent_addresses(self,remote_agent_addresses:list[str]):
        async with asyncio.TaskGroup() as task_group:
            for address in remote_agent_addresses:
                task_group.create_task(self.retrieve_card(address))

    async def retrieve_card(self, address:str):
        card_resolver = A2ACardResolver(self.httpx_client,address)
        card = await card_resolver.get_agent_card()
        self.register_agent_card(card)

    def register_agent_card(self,card:AgentCard):
        remote_connection = RemoteAgentConnections(self.httpx_client, card)
        self.remote_agent_connections[card.name] = remote_connection
        self.cards[card.name] = card
        agent_info = []
        for remote_agent in self.list_remote_agents():
            agent_info.append(json.dumps(remote_agent))
        self.agents = '\n'.join(agent_info)

    def list_remote_agents(self):
        """List the available remote agents you can use to delegate the task."""
        if not self.remote_agent_connections:
            return []

        remote_agent_info = []
        for card in self.cards.values():
            remote_agent_info.append(
                {'name': card.name, 'description': card.description}
            )
        return remote_agent_info
    
    @tool
    def lang_list_remote_agents(self):
        """List the available remote agents you can use to delegate the task."""
        if not self.remote_agent_connections:
            return []

        remote_agent_info = []
        for card in self.cards.values():
            remote_agent_info.append(
                {'name': card.name, 'description': card.description}
            )
        return remote_agent_info
    
    @tool
    async def send_message_2_agent(self,query:str,agent_name:str):
        try:
            response = await self.remote_agent_connections[agent_name].send_message_agent(query)
            return response
        except Exception as e:
            return f"Error in response: {e}"

    def create_agent(self):
        self.tools = [self.lang_list_remote_agents, self.send_message_2_agent]
        self.art_agent = create_react_agent(
            model=self.model,
            tools=self.tools,
            checkpointer=self.memory,
            prompt=self.SYSTEM_INSTRUCTION
        )

    