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
from agent import ArtAgent
from agent_executor import ArtAgentExecutor


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host","host",default="localhost")
@click.option("--port","port",default=9999)
def main(host,port):
    try:
        capabilities = AgentCapabilities(streaming=True,push_notifications=True)
        skill = AgentSkill(
            id="find_word",
            name="Finds synonims for word to use in the poems",
            description="Helps with finding alternative words for creative poems",
            tags=["ideas","words"],
            examples=["Find a synonim for bird"]
        )
        agent_card = AgentCard(
            name="Art agent",
            description="Helps user wirting poems and paragrpahs",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            default_input_modes=ArtAgent.SUPPORTED_CONTENT_TYPES,
            default_output_modes=ArtAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill]
        )

        httpx_client = httpx.AsyncClient()
        push_config_store = InMemoryPushNotificationConfigStore()
        push_sender = BasePushNotificationSender(httpx_client=httpx_client,config_store=push_config_store)
        request_handler = DefaultRequestHandler(
            agent_executor=ArtAgentExecutor(),
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