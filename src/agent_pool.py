import asyncio
import httpx
import logging
from agent_hub import HostAgentHub

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(name=f"Agent.{__name__}")

async def main():
    remote_addresses = [
        "http://localhost:9999/",
        "http://localhost:8888/"
    ]

    async with httpx.AsyncClient(timeout=10.0) as http_client:
        host = HostAgentHub(remote_addresses, http_client)
        main_hub_agent = host.create_agent()

        # Wait until all agents are initialized
        while not host.remote_agent_connections:
            await asyncio.sleep(0.1)

        while True:
            try:
                user_input = input("USER: ")
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break
                response = await host.remote_agent_connections["Art agent"].send_message_agent(user_input)
                print("AGENT:\n",response)
            except Exception as e:
                logger.info(f'General error: {e}')

if __name__ == "__main__":
    asyncio.run(main())
