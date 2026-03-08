import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.scheduler import start_scheduler, stop_scheduler
from app.agent.bootstrap import seed_default_rss_sources
from app.api.agent import router as agent_router
from app.api.auth import router as auth_router
from app.api.comments import router as comments_router
from app.api.news import router as news_router
from app.api.oauth import router as oauth_router
from app.api.posts import router as posts_router
from app.api.upload import router as upload_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed_default_rss_sources()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(oauth_router, prefix=settings.API_V1_PREFIX)
app.include_router(posts_router, prefix=settings.API_V1_PREFIX)
app.include_router(upload_router, prefix=settings.API_V1_PREFIX)
app.include_router(comments_router, prefix=settings.API_V1_PREFIX)
app.include_router(news_router, prefix=settings.API_V1_PREFIX)
app.include_router(agent_router, prefix=settings.API_V1_PREFIX)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
