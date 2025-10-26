"""
FastAPI Main Application
Serves the Cap Table Web App backend with LLM chat, tool execution, and exports.
"""

import sys
import os

# Add parent directory to import cap table modules
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

from webapp.backend.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from webapp.backend.routers import chat, conversation, tools, captable


# Initialize FastAPI app
app = FastAPI(
    title="Cap Table Generator API",
    description="LLM-driven cap table generation with real-time collaboration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(conversation.router)
app.include_router(tools.router)
app.include_router(captable.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Cap Table Generator API",
        "version": "1.0.0",
        "provider": settings.active_provider,
        "model": settings.active_model
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True
    )
