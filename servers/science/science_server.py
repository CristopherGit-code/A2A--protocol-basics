import click, httpx,uvicorn,logging,sys
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from agent import ScienceAgent
from agent_executor import ScienceAgentExecutor


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host","host",default="localhost")
@click.option("--port","port",default=8888)
def main(host,port):
    try:
        capabilities = AgentCapabilities(streaming=True,push_notifications=True)
        skill = AgentSkill(
            id="get_definition",
            name="Gets the word definition for a term",
            description="Helps getting definition for unknown terms",
            tags=["definition","words"],
            examples=["What is the meaning of LamBot?"]
        )
        agent_card = AgentCard(
            name="Science agent",
            description="Helps user write scientific papers or paragraphs",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            default_input_modes=ScienceAgent.SUPPORTED_CONTENT_TYPES,
            default_output_modes=ScienceAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill]
        )

        httpx_client = httpx.AsyncClient()
        push_config_store = InMemoryPushNotificationConfigStore()
        push_sender = BasePushNotificationSender(httpx_client=httpx_client,config_store=push_config_store)
        request_handler = DefaultRequestHandler(
            agent_executor=ScienceAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_config_store=push_config_store,
            push_sender= push_sender
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )

        uvicorn.run(server.build(), host=host, port=port)

    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()