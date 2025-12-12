from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "MultiTenantOrgAPI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # MongoDB Settings
    MONGO_URL: str
    MASTER_DB_NAME: str = "MasterDB"
    ORG_COLLECTION_NAME: str = "organizations"
    ADMIN_COLLECTION_NAME: str = "admin_users"

    class Config:
        env_file = ".env"

settings = Settings()