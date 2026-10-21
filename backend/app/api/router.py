from fastapi import APIRouter

from app.api.routes import auth, connections, health, posts

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth/linkedin", tags=["LinkedIn OAuth"])
api_router.include_router(connections.router, prefix="/connections", tags=["Connections"])
api_router.include_router(posts.router, prefix="/posts", tags=["Scheduled posts"])
