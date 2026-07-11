from fastapi import APIRouter

from app.api.v1 import (
    apis,
    auth,
    docs,
    endpoints,
    invitations,
    organizations,
    projects,
    rest_client,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(organizations.router)
api_router.include_router(invitations.router)
api_router.include_router(projects.router)
api_router.include_router(apis.router)
api_router.include_router(endpoints.router)
api_router.include_router(rest_client.router)
api_router.include_router(docs.router)
