
"""
expose the langraph agent as a REST API

endpoints 
    POST /chat - send a message, get an answer
    GET /health - check if service is running
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent.graph import run_agent
from db.database import test_connection
import uvicorn
import os
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_ok = test_connection()
    print(f"[Startup] Database : {'connected' if db_ok else 'disconnected'}")
    print(f"[Startup] AI Service: running")
    print(f"[Startup] Docs : http://localhost:8000/docs")

    yield

    print("[Shutdown] ERP Copilot shutting down")


app = FastAPI(
    title="ERP Copilot AI Service",
    description="Langraph agent  for retail and whole business intelligence",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://ai.ghanimenterprises.lk",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    tool_used: str
    params: dict
    reasoning: str

@app.get("/health")
def health_check():
    """
     check if service and db are running
    """
    db_ok = test_connection()

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "erp-copilot-ai",
        "database": "connected" if db_ok else "disconnected",
        "version": "1.0.0"
    }

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    send a message to the ERP Copilot agent.
    Returns a natural language answer.
    """
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )
    
    try:
        result = run_agent(request.message)
        return ChatResponse(
            response=result["response"],
            tool_used=result["tool_used"],
            params=result["params"],
            reasoning=result.get("reasoning", "")
        )
    except Exception as e: 
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )
    

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )