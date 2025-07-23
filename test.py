import asyncio
from collections.abc import AsyncIterable
from typing import Any, Literal

import httpx

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from server.modules.oci_client import LLM_Client


# --- Tool Definition ---

@tool(description="Get exchange rate using Frankfurter API.")
def get_exchange_rate(
    currency_from: str = 'USD',
    currency_to: str = 'EUR',
    currency_date: str = 'latest',
) -> dict:
    """Get current exchange rate from Frankfurter API."""
    try:
        response = httpx.get(
            f'https://api.frankfurter.app/{currency_date}',
            params={'from': currency_from, 'to': currency_to},
        )
        response.raise_for_status()
        data = response.json()
        if 'rates' not in data:
            return {'error': 'Invalid API response format.'}
        return data
    except Exception as e:
        return {'error': str(e)}


# --- Response Format for final output ---

class ResponseFormat(BaseModel):
    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str


# --- System and Format Instructions ---

SYSTEM_INSTRUCTION = (
    'You are a specialized assistant for currency conversions. '
    "Your sole purpose is to use the 'get_exchange_rate' tool to answer questions about currency exchange rates. "
    'If the user asks about anything other than currency conversion or exchange rates, '
    'politely state that you cannot help with that topic.'
)

FORMAT_INSTRUCTION = (
    'Set response status to input_required if the user needs to provide more information. '
    'Set response status to error if there is an error. '
    'Set response status to completed if the request is complete.'
)


# --- LLM and Graph Setup ---

llm = LLM_Client().build_llm_client()
tools = [get_exchange_rate]
memory = MemorySaver()

graph = create_react_agent(
    llm,
    tools=tools,
    checkpointer=memory,
    prompt=SYSTEM_INSTRUCTION,
    response_format=(FORMAT_INSTRUCTION, ResponseFormat),
)


# --- Streaming Function ---

async def stream(query: str, context_id: str) -> AsyncIterable[dict[str, Any]]:
    inputs = {'messages': [HumanMessage(content=query)]}
    config = {'configurable': {'thread_id': context_id}}

    for item in graph.stream(inputs, config, stream_mode='values'):
        messages = item.get("messages", [])
        if not messages:
            continue

        last_message = messages[-1]

        if isinstance(last_message, AIMessage) and getattr(last_message, 'tool_calls', []):
            yield {
                'is_task_complete': False,
                'require_user_input': False,
                'content': 'Looking up the exchange rates...',
            }

        elif isinstance(last_message, ToolMessage):
            yield {
                'is_task_complete': False,
                'require_user_input': False,
                'content': 'Processing the exchange rates...',
            }

        elif isinstance(last_message, AIMessage):
            yield {
                'is_task_complete': False,
                'require_user_input': False,
                'content': last_message.content,
            }

    yield get_agent_response(config)


# --- Final Response Helper ---

def get_agent_response(config: dict) -> dict[str, Any]:
    current_state = graph.get_state(config)
    structured_response = current_state.values.get("structured_response")

    if isinstance(structured_response, ResponseFormat):
        return {
            'is_task_complete': structured_response.status == 'completed',
            'require_user_input': structured_response.status == 'input_required',
            'content': structured_response.message,
        }

    return {
        'is_task_complete': False,
        'require_user_input': True,
        'content': 'Unable to process your request.',
    }


# --- Main Execution for Testing ---

if __name__ == "__main__":
    async def run_test():
        query = "How much is 10 USD in INR?"
        print(f"User: {query}\n")
        async for response in stream(query, context_id="session-1"):
            print("Assistant:", response["content"])

    asyncio.run(run_test())
