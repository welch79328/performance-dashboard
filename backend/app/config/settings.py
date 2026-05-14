from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    monday_api_token: str = ""
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    users_config: str = "[]"
    cache_ttl_seconds: int = 900  # 15 minutes

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
