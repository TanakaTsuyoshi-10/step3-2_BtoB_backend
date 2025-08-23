from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.database import SessionLocal
from app.schemas.user import UserCreate
from app.services.user import user_service


@asynccontextmanager
async def lifespan(app):
    print("アプリケーション起動中...")
    
    # Log database connection info (host only, no credentials)
    database_url = settings.sqlalchemy_uri_clean
    if "@" in database_url and ":" in database_url:
        # Extract host from URL (format: mysql+pymysql://user:pass@host:port/db)
        host_part = database_url.split("@")[1].split("/")[0].split(":")[0]
        print(f"データベースホスト: {host_part}")
    
    try:
        # Test database connection first
        try:
            with SessionLocal() as db:
                db.execute(text("SELECT 1"))
            print("✅ データベース接続確認成功")
        except Exception as db_error:
            print(f"❌ データベース接続エラー: {db_error}")
            # Don't fail the app startup, just log the error
            print("⚠️  警告: データベース接続に失敗しましたが、アプリケーションを起動します")
        
        # Create first superuser if configured and database is available
        if settings.FIRST_SUPERUSER_EMAIL and settings.FIRST_SUPERUSER_PASSWORD:
            try:
                with SessionLocal() as db:
                    existing_user = user_service.get_by_email(db, email=settings.FIRST_SUPERUSER_EMAIL)
                    if not existing_user:
                        print(f"初期管理者ユーザーを作成中: {settings.FIRST_SUPERUSER_EMAIL}")
                        user_service.create(
                            db,
                            obj_in=UserCreate(
                                email=settings.FIRST_SUPERUSER_EMAIL,
                                password=settings.FIRST_SUPERUSER_PASSWORD,
                                full_name="システム管理者",
                                is_active=True,
                                is_superuser=True,
                            ),
                        )
                        print("初期管理者ユーザーの作成完了")
                    else:
                        print(f"管理者ユーザー {settings.FIRST_SUPERUSER_EMAIL} は既に存在します")
            except Exception as user_error:
                print(f"初期管理者ユーザー作成エラー: {user_error}")
                print("警告: 初期管理者ユーザーの作成に失敗しましたが、アプリケーションを起動します")
        
        print("アプリケーション起動完了")
    except Exception as e:
        print(f"起動時エラー: {e}")
        # Log error but don't prevent app startup
        print("警告: 起動時にエラーが発生しましたが、アプリケーションを起動します")
    finally:
        yield
        print("アプリケーション終了中...")


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
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Energy Management System API"}


@app.get("/health")
def health_check():
    """Enhanced health check with detailed database status"""
    from datetime import datetime
    
    health_status = {
        "status": "healthy",
        "app": "エネルギーマネージャー API",
        "version": settings.PROJECT_VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Database connection test with more details
    try:
        with SessionLocal() as db:
            result = db.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            if row and row[0] == 1:
                health_status["database"] = {
                    "status": "ok",
                    "message": "接続正常"
                }
            else:
                health_status["database"] = {
                    "status": "error", 
                    "message": "クエリ結果が不正"
                }
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["database"] = {
            "status": "error",
            "message": f"接続エラー: {str(e)[:400]}"
        }
        health_status["status"] = "degraded"
    
    return health_status