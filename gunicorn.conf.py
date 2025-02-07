import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes - More conservative calculation
workers = min(multiprocessing.cpu_count() + 1, 4)  # Max 4 workers
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# Log rotation
logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'generic',
            'stream': 'ext://sys.stdout'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'generic',
            'filename': 'logs/error.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'access_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'access',
            'filename': 'logs/access.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'formatters': {
        'generic': {
            'format': '%(asctime)s [%(process)d] [%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'class': 'logging.Formatter'
        },
        'access': {
            'format': '%(asctime)s [%(process)d] [ACCESS] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'class': 'logging.Formatter'
        }
    },
    'loggers': {
        'gunicorn.error': {
            'level': 'INFO',
            'handlers': ['console', 'error_file'],
            'propagate': False,
            'qualname': 'gunicorn.error'
        }
    }
}

# Process naming
proc_name = 'sgk_export'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None 