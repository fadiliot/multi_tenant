from fastapi import FastAPI
from app.api import org
from app.db.mongo_client import db_client
from app.core.config import settings

def create_app():
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Startup and Shutdown Events for DB
    @app.on_event("startup")
    async def startup_event():
        db_client.connect()

    @app.on_event("shutdown")
    async def shutdown_event():
        db_client.close()

    # Include Routers
    app.include_router(org.router, prefix=f"{settings.API_V1_STR}/org", tags=["Organizations"])
    app.include_router(org.router, prefix=f"{settings.API_V1_STR}/admin", tags=["Authentication"])

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    # This is for local development without the `uvicorn app.main:app` command
    uvicorn.run(app, host="0.0.0.0", port=8000)