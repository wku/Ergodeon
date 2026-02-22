import os
from typing import Dict, Any
from litestar import Litestar, post
from pydantic import BaseModel
from openrouter_agent.agent.core import Agent

# Global agent instance (for demo purposes)
# In production, use dependency injection or session management
agent_instance: Agent | None = None

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

def get_agent() -> Agent:
    global agent_instance
    if agent_instance is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        agent_instance = Agent(api_key=api_key)
    return agent_instance

@post("/chat")
async def chat_handler(data: ChatRequest) -> ChatResponse:
    agent = get_agent()
    response = await agent.chat(data.message)
    return ChatResponse(response=response)

app = Litestar(route_handlers=[chat_handler])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
