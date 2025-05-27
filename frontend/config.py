"""
Configuration module for the frontend service.
Centralizes all environment variables and configuration settings.
"""
import os


class Config:
    """Configuration class for frontend settings."""
    
    # Backend API configuration
    BACKEND_URL: str = os.getenv('BACKEND_URL', 'http://fastapi:8001')
    
    # Frontend configuration
    FRONTEND_PORT: int = int(os.getenv('FRONTEND_PORT', '8501'))
    
    # Binance API configuration (for direct API calls)
    BINANCE_API_KEY: str = os.getenv('BINANCE_API_KEY', 'your_api_key')
    BINANCE_API_SECRET: str = os.getenv('BINANCE_API_SECRET',
                                        'your_api_secret')
    
    # Application settings
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    DEBUG: bool = ENVIRONMENT == 'development'
    
    # UI Settings
    PAGE_TITLE: str = "CryptoBotDE"
    PAGE_ICON: str = "🔮"
    LAYOUT: str = "wide"


# Create a singleton instance
config = Config() 