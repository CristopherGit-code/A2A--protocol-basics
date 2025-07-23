from a2a.types import AgentCard, AgentCapabilities, AgentSkill

# Define your agent
class MyAgent:
    SUPPORTED_CONTENT_TYPES = ["text"]
    
    def process(self, query):
        # Your agent logic here
        return f"Processed: {query}"

# Define capabilities and skills
capabilities = [
    Capability(
        type="text-generation",
        description="Generates text responses to user queries"
    )
]

skills = [
    Skill(
        name="text-response",
        description="Responds to text queries with generated text"
    )
]

# Create the agent card
agent_card = AgentCard(
    name="My A2A Agent",
    description="A simple A2A-compatible agent",
    url="http://localhost:5000/",
    version="1.0.0",
    defaultInputModes=MyAgent.SUPPORTED_CONTENT_TYPES,
    defaultOutputModes=MyAgent.SUPPORTED_CONTENT_TYPES,
    capabilities=capabilities,
    skills=skills,
)

# Create and start the server
server = A2AServer(
    agent_card=agent_card,
    task_manager=MyAgentTaskManager(agent=MyAgent()),
    host="localhost",
    port=5000,
)

server.start()