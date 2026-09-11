from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-5"
    max_upload_size_bytes: int = 10 * 1024 * 1024
    max_batch_size: int = 20
    verification_concurrency: int = 4

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
