from fastapi import APIRouter

from app.api.v1 import auth, invitations, organizations, projects, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(organizations.router)
api_router.include_router(invitations.router)
api_router.include_router(projects.router)
