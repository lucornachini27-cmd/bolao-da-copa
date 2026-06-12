from fastapi import APIRouter

from app.api.v1 import admin, auth, bets, matches, ranking, settings, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(bets.router, prefix="/bets", tags=["bets"])
api_router.include_router(ranking.router, prefix="/ranking", tags=["ranking"])
api_router.include_router(settings.router, prefix="/admin/settings", tags=["admin"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
