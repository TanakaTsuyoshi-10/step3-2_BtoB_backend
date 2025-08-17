from fastapi import APIRouter

from app.api.v1.endpoints import login, users, devices, energy_records, reports

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(energy_records.router, prefix="/energy-records", tags=["energy-records"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])