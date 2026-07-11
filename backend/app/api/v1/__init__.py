from fastapi import APIRouter

from app.api.v1 import apis, auth, endpoints, invitations, organizations, projects, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(organizations.router)
api_router.include_router(invitations.router)
api_router.include_router(projects.router)
api_router.include_router(apis.router)
api_router.include_router(endpoints.router)
