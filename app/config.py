import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secure-key-here')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Upload folder configuration for local file storage
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    TEMPLATES_AUTO_RELOAD = True
    
    # NAS storage configuration
    USE_NAS_STORAGE = os.environ.get('USE_NAS_STORAGE', 'False').lower() == 'true'
    NAS_UPLOAD_FOLDER = os.environ.get('NAS_UPLOAD_FOLDER', '\\\\NAS_SERVER\\sgk_export_share\\uploads')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # SQLAlchemy engine configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 30,
        'pool_size': 10,
        'max_overflow': 5,
        'connect_args': {
            'connect_timeout': 10,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
    }

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TEMPLATES_AUTO_RELOAD = False

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 