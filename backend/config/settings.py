from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # API Keys
    groq_api_key: str
    openai_api_key: str = ""
    
    # Database Configuration
    chroma_db_host: str = "localhost"
    chroma_db_port: int = 8000
    chroma_db_path: str = "./vector_store"
    
    # Application Configuration
    port: int = 8000
    environment: str = "development"
    
    # Scraping Configuration
    groww_base_url: str = "https://groww.in"
    scraping_delay: int = 2
    max_retries: int = 3
    
    # Groww Fund URLs
    fund_urls: List[str] = [
        "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
    ]
    
    # Monitoring
    notification_webhook: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
