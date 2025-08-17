from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.database import SessionLocal
from app.schemas.user import UserCreate
from app.services.user import user_service


@asynccontextmanager
async def lifespan(app):
    try:
        # Create first superuser if configured
        if settings.FIRST_SUPERUSER_EMAIL and settings.FIRST_SUPERUSER_PASSWORD:
            with SessionLocal() as db:
                existing_user = user_service.get_by_email(db, email=settings.FIRST_SUPERUSER_EMAIL)
                if not existing_user:
                    print(f"Creating first superuser: {settings.FIRST_SUPERUSER_EMAIL}")
                    user_service.create(
                        db,
                        obj_in=UserCreate(
                            email=settings.FIRST_SUPERUSER_EMAIL,
                            password=settings.FIRST_SUPERUSER_PASSWORD,
                            full_name="Admin",
                            is_active=True,
                            is_superuser=True,
                        ),
                    )
                    print("First superuser created successfully")
                else:
                    print(f"Superuser {settings.FIRST_SUPERUSER_EMAIL} already exists")
    except Exception as e:
        print(f"Error during startup: {e}")
    finally:
        yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
cors_origins = settings.get_cors_origins()
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Energy Management System API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}