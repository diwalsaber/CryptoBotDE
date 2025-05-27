"""
Configuration module for the backend service.
Centralizes all environment variables and configuration settings.
"""
import os
from typing import Optional


class Config:
    """Configuration class for backend settings."""
    
    # Database configuration
    DB_HOST: str = os.getenv('DB_HOST', 'timescaledb')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'postgres')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'postgres')
    
    # API configuration
    BACKEND_HOST: str = os.getenv('BACKEND_HOST', '0.0.0.0')
    BACKEND_PORT: int = int(os.getenv('BACKEND_PORT', '8001'))
    
    # Binance API configuration (if needed in backend)
    BINANCE_API_KEY: Optional[str] = os.getenv('BINANCE_API_KEY')
    BINANCE_API_SECRET: Optional[str] = os.getenv('BINANCE_API_SECRET')
    
    # Application settings
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    DEBUG: bool = ENVIRONMENT == 'development'
    
    # Model paths
    MODEL_PATH: str = os.getenv('MODEL_PATH', 'lstm.h5')
    SCALER_PATH: str = os.getenv('SCALER_PATH', 'scaler.job')
    
    @classmethod
    def get_db_connection_string(cls) -> str:
        """Generate PostgreSQL connection string."""
        return (f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@"
                f"{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}")
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate that all required configuration is present."""
        required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD']
        missing = []
        
        for var in required_vars:
            if not getattr(cls, var, None):
                missing.append(var)
        
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}")


# Create a singleton instance
config = Config() 