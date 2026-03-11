"""
FastAPI REST API for Ergodeon Agent System
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio

from core.orchestrator import CoreOrchestrator
from models.agent import UserRequest, AgentResult
from utils.config import load_config
from utils.logger import setup_logger

# Initialize
app = FastAPI(
    title="Ergodeon Agent System API",
    description="REST API for Ergodeon AI-powered development agents",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logger
logger = setup_logger(__name__)

# Global orchestrator
orchestrator: Optional[CoreOrchestrator] = None


# Models
class RequestModel(BaseModel):
    text: str
    user_id: str = "api-user"
    session_id: str = "api-session"


class ResponseModel(BaseModel):
    status: str
    output: str
    files_created: list = []
    files_modified: list = []
    error: Optional[str] = None


# Startup/Shutdown
@app.on_event("startup")
async def startup():
    """Initialize orchestrator"""
    global orchestrator
    
    try:
        config = load_config()
        orchestrator = CoreOrchestrator(config)
        await orchestrator.initialize()
        logger.info("Orchestrator initialized")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Shutdown orchestrator"""
    global orchestrator
    
    if orchestrator:
        await orchestrator.shutdown()
        logger.info("Orchestrator shutdown")


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Ergodeon Agent System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "orchestrator": "initialized" if orchestrator else "not initialized"
    }


@app.post("/api/request", response_model=ResponseModel)
async def process_request(request: RequestModel):
    """Process user request"""
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        # Create user request
        user_request = UserRequest(
            text=request.text,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Process
        result = await orchestrator.process_request(user_request)
        
        # Return response
        return ResponseModel(
            status=result.status,
            output=result.output,
            files_created=result.files_created,
            files_modified=result.files_modified,
            error=result.error
        )
        
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/specs")
async def list_specs():
    """List all specs"""
    # TODO: Implement spec listing
    return {"specs": []}


@app.get("/api/specs/{spec_name}")
async def get_spec(spec_name: str):
    """Get spec details"""
    # TODO: Implement spec retrieval
    return {"spec": spec_name, "status": "not implemented"}


@app.post("/api/specs/{spec_name}/tasks/{task_id}/execute")
async def execute_task(spec_name: str, task_id: str):
    """Execute specific task"""
    # TODO: Implement task execution
    return {"task": task_id, "status": "not implemented"}


@app.get("/api/agents")
async def list_agents():
    """List available agents"""
    return {
        "agents": [
            "general-task-execution",
            "context-gatherer",
            "spec-task-execution",
            "feature-requirements-first-workflow",
            "feature-design-first-workflow",
            "bugfix-workflow",
            "custom-agent-creator"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
