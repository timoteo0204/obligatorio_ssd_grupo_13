from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    excel_path: str = "/data/dataset.xlsx"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:1b"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    server_port: int = 8000
    vectorstore_path: str = "/data/vectorstore"
    mongo_uri: str = "mongodb://mongodb:27017/retail360"
    retriever_search_type: str = "similarity"
    retriever_k: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
