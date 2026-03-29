from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'pharma-backend'
    debug: bool = True
    api_prefix: str = '/api/v1'
    host: str = '0.0.0.0'
    port: int = 8000

    jwt_secret: str = 'supersecret'
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60

    sqlite_db_path: str = 'sqlite:///./data/auth.db'

    neo4j_uri: str = 'bolt://host.docker.internal:7688'
    neo4j_username: str = 'neo4j'
    neo4j_password: str = 'change_me'
    neo4j_database: str = 'neo4j'

    log_level: str = 'INFO'


@lru_cache
def get_settings() -> Settings:
    return Settings()
