from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from server.modules.oci_client import LLM_Client

# --8<-- [start:HelloWorldAgent]
class HelloWorldAgent:
    """Hello World Agent."""
    def __init__(self):
        self.llm = LLM_Client()
        self.agent = self.llm.build_llm_client()

    async def invoke(self,context:RequestContext) -> str:
        # message = context.message
        # message_context = context.call_context
        # print(message.parts)
        # print(message_context)
        user_input = context.get_user_input()
        # response = self.agent.invoke(user_input)
        return f"Hello, yout request was: {user_input}"

# --8<-- [end:HelloWorldAgent]

# --8<-- [start:HelloWorldAgentExecutor_init]
class HelloWorldAgentExecutor(AgentExecutor):
    """Test AgentProxy Implementation."""

    def __init__(self):
        self.agent = HelloWorldAgent()

    # --8<-- [end:HelloWorldAgentExecutor_init]
    # --8<-- [start:HelloWorldAgentExecutor_execute]
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        result = await self.agent.invoke(context)
        await event_queue.enqueue_event(new_agent_text_message(result))

    # --8<-- [end:HelloWorldAgentExecutor_execute]

    # --8<-- [start:HelloWorldAgentExecutor_cancel]
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')

    # --8<-- [end:HelloWorldAgentExecutor_cancel]