
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
 
from app.core.config import get_settings
from app.core.db import get_mongo_client, get_qdrant_client
from app.core.security import get_current_user
 
from app.api import auth as auth_router
from app.api import models as models_router
from app.api import knowledge as knowledge_router
from app.api import chat as chat_router
from app.api import config as config_router
from app.api import endpoints as endpoints_router
from app.api import inference as inference_router
from app.api import history as history_router
from app.api import playground as playground_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.jwt_secret_key)

# --- Public routers ---
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(models_router.router, prefix="/models", tags=["models"])
app.include_router(inference_router.router, prefix="/inference", tags=["inference"])

# -- Protected routers (require authentication) ---
app.include_router(knowledge_router.router, prefix="/knowledge", tags=["knowledge"], dependencies=[Depends(get_current_user)],)
app.include_router(config_router.router, prefix="/config", tags=["config"], dependencies=[Depends(get_current_user)],)
app.include_router(endpoints_router.router, prefix="/endpoints", tags=["endpoints"], dependencies=[Depends(get_current_user)],)
app.include_router(
    playground_router.router, prefix="/playground", tags=["playground"],
    dependencies=[Depends(get_current_user)],
)

# Already needs user auth, so no need to add Depends(get_current_user) here
app.include_router(chat_router.router, prefix="/chat", tags=["chat"])
app.include_router(history_router.router, prefix="/history", tags=["history"])

@app.get("/health")
def health_check():
    """Basic liveness check — confirms the API is up and settings load correctly."""
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.environment,
    }

@app.get("/health/dependencies")
def dependency_health_check():
    """Checks that Qdrant and MongoDB are actually reachable, not just configured."""
    status = {"mongo": "unknown", "qdrant": "unknown"}
 
    try:
        get_mongo_client().admin.command("ping")
        status["mongo"] = "ok"
    except Exception as e:
        status["mongo"] = f"error: {e}"
 
    try:
        get_qdrant_client().get_collections()
        status["qdrant"] = "ok"
    except Exception as e:
        status["qdrant"] = f"error: {e}"
 
    overall = "ok" if all(v == "ok" for v in status.values()) else "degraded"
    return {"status": overall, "dependencies": status}
 