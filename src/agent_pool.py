import asyncio
import httpx
import logging
from agent_hub import HostAgentHub

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(name=f"Agent.{__name__}")

def stream_updates(user_input: str) -> str:
    """Creates a custom workflow to fulfill the user's request using a variety of agents"""
    final_response = []
    try:
        for chunk in supervisor.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            {"configurable": {"thread_id": "1"},"callbacks":[fuse_config.get_handler()], "metadata":{"langfuse_session_id":id}},
            stream_mode="values",
            subgraphs=True
        ):
            logger.debug("=============== current chunk ===============")
            logger.debug(chunk[-1]['messages'][-1])
            try:
                final_response.append(chunk[-1]['messages'][-1].content)
            except Exception as p:
                final_response.append(f"Error in response: {p}")
    except Exception as e:
        logger.debug(e)
        final_response.append(f"Error in response: {e}")
    return final_response[-1]

async def main():
    # Add all remote server address, also the VM
    remote_addresses = [
        "http://localhost:9999/",
        "http://localhost:8888/"
    ]

    async with httpx.AsyncClient(timeout=10.0) as http_client:
        host = HostAgentHub(remote_addresses, http_client)
        host.create_agent()

        # Wait until all agents are initialized
        while not host.remote_agent_connections:
            await asyncio.sleep(0.1)

        while True:
            try:
                user_input = input("USER: ")
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break
                final_response = []
                async for chunk in host.hub_agent.astream( {"messages": [{"role": "user", "content": user_input}]},
                    {"configurable": {"thread_id": "1"}},
                    stream_mode="values",
                    subgraphs=True
                ):
                    logger.debug("Chunk response ==========")
                    logger.debug(chunk[-1]['messages'][-1])
                    try:
                        final_response.append(chunk[-1]['messages'][-1].content)
                    except Exception as p:
                        final_response.append(f"Error in response: {p}")
                print("MODEL RESPONSE")
                print(final_response[-1])
            except Exception as e:
                logger.info(f'General error: {e}')

if __name__ == "__main__":
    asyncio.run(main())
