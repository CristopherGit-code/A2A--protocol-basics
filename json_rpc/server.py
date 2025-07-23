from starlette.applications import Starlette
from starlette.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request
import uvicorn
import json
from typing import AsyncIterable

# Import A2A types (you would typically use the A2A library)
from a2a.types import (
    AgentCard,
    A2ARequest,
    GetTaskRequest,
    SendTaskRequest,
    SendTaskStreamingRequest,
    TaskManager
)

class A2AServer:
    def __init__(
        self,
        host="0.0.0.0",
        port=5000,
        endpoint="/",
        agent_card=None,
        task_manager=None,
    ):
        self.host = host
        self.port = port
        self.endpoint = endpoint
        self.task_manager = task_manager
        self.agent_card = agent_card
        self.app = Starlette()
        
        # Set up routes
        self.app.add_route(self.endpoint, self._process_request, methods=["POST"])
        self.app.add_route(
            "/.well-known/agent.json", self._get_agent_card, methods=["GET"]
        )

    def start(self):
        # Validate required components
        if self.agent_card is None:
            raise ValueError("agent_card is not defined")
        if self.task_manager is None:
            raise ValueError("task_manager is not defined")
            
        # Start the server
        uvicorn.run(self.app, host=self.host, port=self.port)

    def _get_agent_card(self, request: Request) -> JSONResponse:
        # Return the agent card as JSON
        return JSONResponse(self.agent_card.model_dump(exclude_none=True))

    async def _process_request(self, request: Request):
        try:
            # Parse the JSON-RPC request
            body = await request.json()
            json_rpc_request = A2ARequest.validate_python(body)

            # Route to the appropriate handler based on request type
            if isinstance(json_rpc_request, GetTaskRequest):
                result = await self.task_manager.on_get_task(json_rpc_request)
            elif isinstance(json_rpc_request, SendTaskRequest):
                result = await self.task_manager.on_send_task(json_rpc_request)
            elif isinstance(json_rpc_request, SendTaskStreamingRequest):
                result = await self.task_manager.on_send_task_subscribe(
                    json_rpc_request
                )
            # Handle other request types...
            
            # Return the result
            if isinstance(result, AsyncIterable):
                return EventSourceResponse(result)
            else:
                return JSONResponse(result.model_dump(exclude_none=True))
                
        except Exception as e:
            # Handle errors
            return JSONResponse({"error": str(e)}, status_code=500)