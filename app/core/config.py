from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    app_name: str = "Robotics RT Stack"
    database_url: str = Field(
        default="postgresql+asyncpg://robotics:robotics@localhost:5432/robotics"
    )
    sync_database_url: str = Field(
        default="postgresql+psycopg://robotics:robotics@localhost:5432/robotics"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672/")
    rabbitmq_max_retries: int = Field(default=3)
    mqtt_host: str = Field(default="localhost")
    mqtt_port: int = Field(default=1883)
    elastic_url: str = Field(default="http://localhost:9200")
    metrics_namespace: str = "robotics_rt"
    prometheus_enabled: bool = True
    messaging_enabled: bool = Field(default=True)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
