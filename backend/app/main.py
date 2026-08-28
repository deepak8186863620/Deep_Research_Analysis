from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import connect_to_mongo, close_mongo_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to MongoDB on startup
    await connect_to_mongo()
    yield
    # Close MongoDB connection on shutdown
    await close_mongo_connection()


app = FastAPI(
    title="Deep Research Analysis API",
    description="AI-powered research synthesis using Semantic Scholar + Tavily + Gemini",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS — allow localhost dev ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",  # Keep wildcard for flexibility during dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api import research
app.include_router(research.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Deep Research Analysis API is running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
    