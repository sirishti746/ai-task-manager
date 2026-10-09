from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    # Required: the app refuses to start if these are missing from .env
    DATABASE_URL: str
    JWT_SECRET_KEY: str  
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    AI_API_KEY: str = ""
    AI_MODEL: str = "gemini-2.5-flash"
    AI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    AI_TIMEOUT_SECONDS: float = 15.0  
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()