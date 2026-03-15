from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/interview_eval"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenRouter / LLM
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4.1-mini"

    # Versioning
    question_prompt_version: str = "v1"
    evaluation_prompt_version: str = "v1"
    evaluation_schema_version: str = "v1"
    rubric_version: str = "v1"

    # Tuning
    question_generation_timeout: int = 30
    evaluation_timeout: int = 60
    max_questions_per_session: int = 10
    log_level: str = "INFO"


settings = Settings()
