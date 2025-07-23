import asyncio
from typing import AsyncIterable, Dict
from a2a.types import (
    Task,
    TaskSendParams,
    TaskStatus,
    TaskState,
    SendTaskResponse,
    GetTaskResponse,
    SendTaskStreamingResponse
)

class InMemoryTaskManager:
    def __init__(self):
        self.tasks = {}
        self.lock = asyncio.Lock()

    async def upsert_task(self, task_send_params: TaskSendParams) -> Task:
        async with self.lock:
            task = self.tasks.get(task_send_params.id)
            if task is None:
                # Create a new task
                task = Task(
                    id=task_send_params.id,
                    sessionId=task_send_params.sessionId,
                    messages=[task_send_params.message],
                    status=TaskStatus(state=TaskState.SUBMITTED),
                    history=[task_send_params.message],
                )
                self.tasks[task_send_params.id] = task
            else:
                # Update existing task
                task.history.append(task_send_params.message)
            return task

    async def on_send_task(self, request) -> SendTaskResponse:
        # Validate the request
        # Process the task
        # Return a response
        pass

    async def on_get_task(self, request) -> GetTaskResponse:
        # Retrieve and return task status
        pass

    async def on_send_task_subscribe(self, request) -> AsyncIterable[SendTaskStreamingResponse]:
        # Set up streaming response
        # Yield updates as they occur
        pass

class MyAgentTaskManager(InMemoryTaskManager):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent

    async def on_send_task(self, request):
        # Validate the request
        error = self._validate_request(request)
        if error:
            return error
            
        # Create or update the task
        await self.upsert_task(request.params)
        
        # Process the task with your agent
        task_id = request.params.id
        user_message = request.params.message
        
        # Extract the user query
        user_query = self._get_user_query(request.params)
        
        # Process with your agent
        response = self.agent.process(user_query)
        
        # Update task status and create response
        task = await self._update_task_with_response(task_id, response)
        
        # Return the response
        return SendTaskResponse(
            id=request.id,
            result=task
        )