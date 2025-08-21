from fastapi import APIRouter

from app.api.v1.endpoints import login, users, devices, energy_records, reports, points, rewards, admin, metrics, incentives, auto_report

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(energy_records.router, prefix="/energy-records", tags=["energy-records"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(points.router, prefix="/points", tags=["points"])
api_router.include_router(rewards.router, prefix="/rewards", tags=["rewards"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(incentives.router, prefix="/incentives", tags=["incentives"])
api_router.include_router(auto_report.router, prefix="/reports", tags=["auto-reports"])