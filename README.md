# A2A basic communication

> [!NOTE]  
> Last update 7-25-2025

An A2A program with conection of two different expertise AI agents

## Features

- [supervisor](main.py) The agent connection pool to fetch the remote agents and their capabilities
- [agents](test) Host agent to receive the user request and decide to call the remote server agents
- Terminal based UI
- [servers](servers) Different servers with AI langgraph agents expert in one category (art, science)
- A2A connection. Via ```SendMessageRequest``` the host agent makes HTTPX client ```POST``` and ```GET``` requests to the AI agents in the servers

## Setup

1. Get the necessary dependencies (use python venv / toml)
2. Create .env file to set the environment variables for OCI setup (also mutable to other LLM providers given API key)
    - Ensure to modify the file [yaml](src/modules/config/config.yaml) to add routes and variables
    - Check the other files in servers folder
3. Run each server from cmd [art_server](servers/art/art_server.py) and [science_server](servers/science/science_server.py)
4. Ensure the right connections to server ports in the main [agent_pool](src/agent_pool.py) start to reach the right servers
5. Wait for remote servers to connect and send some questions to the agent in pool connection to respond

## Basic walkthrough

- [Demo video](walkthrough/A2A_demo.mp4)
- [Architecture](walkthrough/A2A%20basic%20architecture.png)