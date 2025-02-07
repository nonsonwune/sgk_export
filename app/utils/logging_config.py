import os
import logging.config
import logging.handlers

def ensure_log_directory():
    """Ensure the logs directory exists"""
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

class MainProcessFilter(logging.Filter):
    def filter(self, record):
        return os.environ.get('GUNICORN_WORKER_PROCESS') != 'true'

class BinaryFilter(logging.Filter):
    """Filter out binary data from logs"""
    def filter(self, record):
        try:
            # Check if the message contains binary data
            record.msg.encode('utf-8').decode('utf-8')
            return True
        except (UnicodeError, AttributeError):
            return False

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_main_process': {
            '()': 'app.utils.logging_config.MainProcessFilter'
        },
        'filter_binary': {
            '()': 'app.utils.logging_config.BinaryFilter'
        }
    },
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] [PID:%(process)d] [%(name)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'filters': ['filter_binary']
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(ensure_log_directory(), 'app.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8',
            'filters': ['filter_binary']
        },
        'error_file': {
            'level': 'ERROR',
            'formatter': 'standard',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(ensure_log_directory(), 'error.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8',
            'filters': ['filter_binary']
        },
        'access_file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(ensure_log_directory(), 'access.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8',
            'filters': ['filter_binary']
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': True
        },
        'gunicorn.access': {
            'handlers': ['access_file'],
            'level': 'INFO',
            'propagate': False
        },
        'gunicorn.error': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False
        }
    }
}

def setup_logging():
    """Initialize logging configuration"""
    try:
        ensure_log_directory()
        
        # Add binary filter to all handlers
        for handler in LOGGING_CONFIG['handlers'].values():
            if 'filters' not in handler:
                handler['filters'] = []
            handler['filters'].append('filter_binary')
        
        logging.config.dictConfig(LOGGING_CONFIG)
        logging.info('Logging setup completed successfully')
    except Exception as e:
        print(f'Error setting up logging: {str(e)}')
        raise 