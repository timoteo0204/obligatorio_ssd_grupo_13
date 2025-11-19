from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    excel_path: str = "/data/dataset.xlsx"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3"
    embedding_model: str = "llama3"
    server_port: int = 8000
    vectorstore_path: str = "/data/vectorstore"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
