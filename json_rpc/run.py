import asyncio
from uuid import uuid4

async def main():
    # Create a client
    client = A2AClient(url="http://localhost:5000/")
    
    # Generate a unique task ID
    task_id = str(uuid4())
    
    # Create a task payload
    payload = {
        "id": task_id,
        "sessionId": str(uuid4()),
        "acceptedOutputModes": ["text"],
        "message": {
            "role": "user",
            "parts": [
                {
                    "type": "text",
                    "text": "Hello, agent!",
                }
            ],
        },
    }
    
    # Send the task
    response = await client.send_task(payload)
    
    # Print the response
    print(f"Response: {response}")

# Run the client
asyncio.run(main())