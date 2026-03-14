"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import chat, conversations, visualize, admin, examples

app = FastAPI(
    title="Strands FIS Agent API",
    description="금융 데이터 분석 AI Agent",
    version="1.0.0",
)

# CORS (BR-08-01)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(visualize.router)
app.include_router(admin.router)
app.include_router(examples.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
