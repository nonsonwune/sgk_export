from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
csrf = CSRFProtect()

# Configure CSRF to accept tokens from both forms and headers
def configure_csrf(app):
    csrf.exempt(app.blueprints.get('api'))
    
    # Configure CSRF to accept X-CSRF-TOKEN header
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    app.config['WTF_CSRF_HEADERS'] = ['X-CSRF-TOKEN'] 