import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "RouteWise AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database: Default to local SQLite for zero-config run, seamlessly supports MySQL via mysql+pymysql://...
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./supplyguard.db")
    
    # Auth Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supplyguard-enterprise-secret-key-2026-hackathon-ibm")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # IBM / Bob AI Service
    IBM_AI_API_KEY: str = os.getenv("IBM_AI_API_KEY", "")
    IBM_BOB_API_URL: str = os.getenv("IBM_BOB_API_URL", "")
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()
