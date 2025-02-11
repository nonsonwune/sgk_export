from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from ..extensions import db
import logging

logger = logging.getLogger(__name__)

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value

class User(UserMixin, db.Model):
    id = db.Column(GUID(), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_superuser = db.Column(db.Boolean, default=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            self.id = str(uuid.uuid4())
        elif not self.is_valid_uuid(self.id):
            logger.warning(f"Invalid UUID format for user ID: {self.id}, generating new UUID")
            self.id = str(uuid.uuid4())
    
    @staticmethod
    def is_valid_uuid(val):
        """Validate UUID format"""
        try:
            uuid.UUID(str(val))
            return True
        except (ValueError, AttributeError):
            return False
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Override get_id to ensure UUID format.
        
        Flask-Login requires the user ID to be returned as a string.
        We validate the UUID format before converting to ensure data integrity.
        """
        if not self.is_valid_uuid(self.id):
            logger.error(f"Invalid UUID format detected for user {self.username}")
            return None
        return str(self.id) 