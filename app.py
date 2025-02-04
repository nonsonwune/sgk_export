from flask import Flask, request, render_template, redirect, url_for, make_response, jsonify, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from weasyprint import HTML, CSS
from weasyprint.urls import URLFetchingError
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
from werkzeug.utils import secure_filename
from datetime import datetime
import base64
import qrcode
import io
from PIL import Image
import fcntl
import time
from sqlalchemy import text
from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.id import ID
from appwrite.input_file import InputFile

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask and extensions
app = Flask(__name__)

# Use environment variable for database URL with fallback to local development
DATABASE_URL = os.environ.get('DATABASE_URL', f'postgresql://{os.environ.get("USER")}@localhost/sgk_export_db')

# If the URL starts with postgres://, replace it with postgresql:// (Render specific fix)
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Use environment variable for secret key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secure-key-here')  # TODO: Change in production

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Add template debugging
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# Add this function after imports
def ensure_upload_dirs():
    """Ensure all required upload directories exist"""
    upload_dirs = ['uploads', 'uploads/sender_signature']
    for directory in upload_dirs:
        os.makedirs(directory, exist_ok=True)

# Add this to your app initialization
ensure_upload_dirs()

# Appwrite configuration
APPWRITE_ENDPOINT = os.environ.get('APPWRITE_ENDPOINT', 'https://cloud.appwrite.io/v1')
APPWRITE_PROJECT_ID = os.environ.get('APPWRITE_PROJECT_ID')
APPWRITE_BUCKET_ID = os.environ.get('APPWRITE_BUCKET_ID')
APPWRITE_API_KEY = os.environ.get('APPWRITE_API_KEY')  # Add API key configuration

def init_appwrite():
    """Initialize Appwrite client"""
    try:
        logger.debug("Initializing Appwrite client...")
        logger.debug(f"Using endpoint: {APPWRITE_ENDPOINT}")
        logger.debug(f"Project ID: {APPWRITE_PROJECT_ID}")
        logger.debug(f"Bucket ID: {APPWRITE_BUCKET_ID}")
        logger.debug("API Key configured: %s", "Yes" if APPWRITE_API_KEY else "No")

        client = Client()
        client.set_endpoint(APPWRITE_ENDPOINT)
        client.set_project(APPWRITE_PROJECT_ID)
        client.set_key(APPWRITE_API_KEY)  # Add API key to client

        # Test connection
        storage = Storage(client)
        logger.info("Appwrite client initialized successfully")
        return storage
    except Exception as e:
        logger.error(f"Failed to initialize Appwrite client: {str(e)}")
        raise

# Initialize Appwrite storage
storage = init_appwrite()

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        logger.debug(f"Password hash set for user {self.username}")
        
    def check_password(self, password):
        logger.debug(f"Checking password for user {self.username}")
        result = check_password_hash(self.password_hash, password)
        logger.debug(f"Password check result: {result}")
        return result

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def create_default_admin():
    """Create default admin user if no users exist"""
    try:
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                name='Administrator',
                is_admin=True
            )
            admin.set_password('admin123')  # Default password should be changed on first login
            db.session.add(admin)
            db.session.commit()
            logger.info('Default admin user created')
        else:
            logger.info('Admin user already exists')
    except Exception as e:
        logger.error(f'Error creating default admin: {str(e)}')
        db.session.rollback()

class ItemDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    export_request_id = db.Column(db.Integer, db.ForeignKey('export_request.id'), nullable=False)
    description = db.Column(db.String(200))
    value = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    weight = db.Column(db.Float)
    image_filename = db.Column(db.String(255))

class ExportRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    waybill_number = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    items = db.relationship('ItemDetail', backref='export_request', lazy=True)
    
    # Sender Information
    sender_name = db.Column(db.String(100), nullable=False)
    sender_email = db.Column(db.String(120))
    sender_address = db.Column(db.String(200))
    sender_business = db.Column(db.String(100))
    sender_mobile = db.Column(db.String(20), nullable=False)
    
    # Receiver Information
    receiver_name = db.Column(db.String(100), nullable=False)
    receiver_email = db.Column(db.String(120))
    receiver_address = db.Column(db.String(200))
    receiver_business = db.Column(db.String(100))
    receiver_mobile = db.Column(db.String(20), nullable=False)
    
    # Destination Details
    destination_address = db.Column(db.String(200))
    destination_country = db.Column(db.String(100))
    destination_postcode = db.Column(db.String(20))
    
    # Pricing Details
    freight_pricing = db.Column(db.Float, default=0)
    additional_charges = db.Column(db.Float, default=0)
    pickup_charge = db.Column(db.Float, default=0)
    handling_fees = db.Column(db.Float, default=0)
    crating = db.Column(db.Float, default=0)
    insurance_charge = db.Column(db.Float, default=0)
    
    # Additional Details
    is_collection = db.Column(db.Boolean, default=False)
    customer_group = db.Column(db.String(100))
    order_booked_by = db.Column(db.String(100))
    sender_signature = db.Column(db.String(500))
    status = db.Column(db.String(50), default='draft')  # draft, saved, completed

    @classmethod
    def generate_waybill_number(cls):
        """Generate the next waybill number in sequence"""
        last_request = cls.query.order_by(cls.id.desc()).first()
        if not last_request:
            return 'WR00001'
        
        last_number = int(last_request.waybill_number[2:])
        next_number = last_number + 1
        return f'WR{next_number:05d}'

# Routes
@app.route('/')
@app.route('/new-export')
@login_required
def new_export():
    logger.debug('Accessing new export form route')
    logger.debug(f'Request path: {request.path}')
    logger.debug(f'Request endpoint: {request.endpoint}')
    try:
        logger.debug('Attempting to render form.html template')
        return render_template('form.html')
    except Exception as e:
        logger.error(f'Error rendering form.html: {str(e)}')
        raise

@app.route('/list')
@login_required
def list_exports():
    exports = ExportRequest.query.order_by(ExportRequest.created_at.desc()).all()
    return render_template('list.html', exports=exports)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        logger.debug(f"Login attempt for username: {username}")
        
        user = User.query.filter_by(username=username).first()
        if user:
            logger.debug(f"User found: {user.username}, is_admin: {user.is_admin}")
            if user.check_password(password):
                logger.debug("Password verification successful")
                login_user(user)
                logger.debug(f"User {username} logged in successfully")
                return redirect(url_for('new_export'))
            else:
                logger.debug("Password verification failed")
                flash('Invalid username or password')
        else:
            logger.debug("User not found")
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin/create-user', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('new_export'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        else:
            new_user = User(username=username, name=name)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('User created successfully')
            return redirect(url_for('new_export'))
            
    return render_template('create_user.html')

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    logger.debug('Processing form submission')
    try:
        # Create a mutable copy of form data
        data = request.form.to_dict()
        logger.debug(f'Received form data: {data}')
        
        # Handle signature data
        signature_file_id = None
        if data.get('sender_signature'):
            signature_data = data.get('sender_signature')
            if signature_data.startswith('data:image/png;base64,'):
                # Generate unique filename
                signature_data = signature_data.split(',')[1]  # Remove data URL prefix
                signature_bytes = base64.b64decode(signature_data)
                
                # Create temporary file for signature
                temp_signature_path = os.path.join('/tmp', f'signature_{datetime.now().strftime("%Y%m%d%H%M%S")}.png')
                with open(temp_signature_path, 'wb') as f:
                    f.write(signature_bytes)
                
                try:
                    # Use Appwrite's InputFile
                    input_file = InputFile.from_path(temp_signature_path)
                    result = storage.create_file(
                        bucket_id=APPWRITE_BUCKET_ID,
                        file_id=ID.unique(),
                        file=input_file
                    )
                    signature_file_id = result['$id']
                    data['sender_signature'] = signature_file_id
                except Exception as e:
                    logger.error(f'Error uploading signature: {str(e)}')
                    raise
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_signature_path):
                        os.remove(temp_signature_path)

        # Create new export request with logged-in user
        new_request = ExportRequest(
            waybill_number=ExportRequest.generate_waybill_number(),
            status='draft',
            order_booked_by=current_user.name,
            
            # Sender Information
            sender_name=data.get('sender_name'),
            sender_email=data.get('sender_email'),
            sender_address=data.get('sender_address'),
            sender_business=data.get('sender_business'),
            sender_mobile=data.get('sender_mobile'),
            
            # Receiver Information
            receiver_name=data.get('receiver_name'),
            receiver_email=data.get('receiver_email'),
            receiver_address=data.get('receiver_address'),
            receiver_business=data.get('receiver_business'),
            receiver_mobile=data.get('receiver_mobile'),
            
            # Destination Details
            destination_address=data.get('destination_address'),
            destination_country=data.get('destination_country'),
            destination_postcode=data.get('destination_postcode'),
            
            # Pricing Details
            freight_pricing=float(data.get('freight', 0) or 0),
            additional_charges=float(data.get('additional', 0) or 0),
            pickup_charge=float(data.get('pickup', 0) or 0),
            handling_fees=float(data.get('handling', 0) or 0),
            crating=float(data.get('crating', 0) or 0),
            insurance_charge=float(data.get('insurance', 0) or 0),
            
            # Additional Details
            is_collection=bool(data.get('is_collection')),
            customer_group=data.get('customer_group'),
            sender_signature=data.get('sender_signature')
        )
        logger.debug(f'Created new export request with waybill: {new_request.waybill_number}')
        
        # Add items
        descriptions = request.form.getlist('description[]')
        values = request.form.getlist('value[]')
        quantities = request.form.getlist('quantity[]')
        weights = request.form.getlist('weight[]')
        images = request.files.getlist('item_image[]')
        
        # Validate at least one item
        if not descriptions or not descriptions[0]:
            error_msg = "Please add at least one item"
            logger.error(f"Validation error: {error_msg}")
            return render_template('form.html', error=error_msg), 400
        
        logger.debug(f'Processing {len(descriptions)} items')
        
        for i in range(len(descriptions)):
            # Skip empty items
            if not descriptions[i]:
                continue
                
            try:
                item = ItemDetail(
                    description=descriptions[i],
                    value=float(values[i] if values[i] else 0),
                    quantity=int(quantities[i] if quantities[i] else 0),
                    weight=float(weights[i] if weights[i] else 0)
                )
                
                # Handle image upload
                if i < len(images) and images[i] and images[i].filename:
                    try:
                        # Save uploaded file temporarily
                        temp_image_path = os.path.join('/tmp', secure_filename(images[i].filename))
                        images[i].save(temp_image_path)
                        
                        # Use Appwrite's InputFile
                        input_file = InputFile.from_path(temp_image_path)
                        result = storage.create_file(
                            bucket_id=APPWRITE_BUCKET_ID,
                            file_id=ID.unique(),
                            file=input_file
                        )
                        item.image_filename = result['$id']
                        
                        # Clean up temporary file
                        os.remove(temp_image_path)
                    except Exception as e:
                        logger.error(f'Error uploading item image: {str(e)}')
                        raise
                
                new_request.items.append(item)
            except (ValueError, TypeError) as e:
                error_msg = f"Invalid value for item {i+1}. Please enter valid numbers."
                logger.error(f"Validation error: {error_msg} - {str(e)}")
                return render_template('form.html', error=error_msg), 400
        
        db.session.add(new_request)
        db.session.commit()
        logger.debug(f'Successfully saved export request {new_request.id}')
        
        return redirect(url_for('preview', id=new_request.id))
    except Exception as e:
        logger.error(f'Error in submit route: {str(e)}')
        return render_template('form.html', error="An error occurred while processing your request."), 500

@app.route('/preview/<int:id>')
def preview(id):
    logger.debug(f'Accessing preview for export request {id}')
    try:
        request_data = ExportRequest.query.get_or_404(id)
        logger.debug(f'Found export request: {request_data.waybill_number}')

        # Generate QR code with optimized data format
        qr_data = f"Waybill: {request_data.waybill_number}, Sender Mobile: {request_data.sender_mobile}, Receiver Mobile: {request_data.receiver_mobile}, Booked By: {request_data.order_booked_by}"
        
        # Create QR code with optimized settings
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to BytesIO
        qr_buffer = io.BytesIO()
        qr_image.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        try:
            # Upload QR code to Appwrite
            qr_file_id = f"qr_{request_data.waybill_number}"
            result = storage.create_file(
                bucket_id=APPWRITE_BUCKET_ID,
                file_id=qr_file_id,
                file=InputFile.from_bytes(
                    qr_buffer.getvalue(),
                    filename=f"{qr_file_id}.png"
                )
            )
            qr_file_id = result['$id']
            logger.debug(f'QR code uploaded with ID: {qr_file_id}')
        except Exception as e:
            logger.error(f'Error uploading QR code: {str(e)}')
            qr_file_id = None

        # Calculate totals
        subtotal = sum([
            request_data.freight_pricing or 0,
            request_data.additional_charges or 0,
            request_data.pickup_charge or 0,
            request_data.handling_fees or 0,
            request_data.crating or 0,
            request_data.insurance_charge or 0
        ])
        logger.debug(f'Calculated subtotal: {subtotal}')

        vat = subtotal * 0.07
        total = subtotal + vat

        logger.debug(f'Calculated VAT: {vat}, Total: {total}')

        return render_template('preview.html',
                            request=request_data,
                            subtotal=subtotal,
                            vat=vat,
                            total=total,
                            qr_code=qr_file_id)
    except Exception as e:
        logger.error(f'Error in preview route: {str(e)}')
        raise

@app.route('/download-pdf/<int:id>')
def download_pdf(id):
    try:
        request_data = ExportRequest.query.get_or_404(id)
        
        # Calculate totals (same as preview route)
        subtotal = sum([
            request_data.freight_pricing or 0,
            request_data.additional_charges or 0,
            request_data.pickup_charge or 0,
            request_data.handling_fees or 0,
            request_data.crating or 0,
            request_data.insurance_charge or 0
        ])
        vat = subtotal * 0.07
        total = subtotal + vat
        
        # Get the base URL for static files
        base_url = request.url_root
        
        # Render template with absolute URLs and financial calculations
        html_content = render_template('preview.html', 
            request=request_data,
            base_url=base_url,
            subtotal=subtotal,
            vat=vat,
            total=total
        )
        
        # Create PDF with proper base URL
        html = HTML(string=html_content, base_url=base_url)
        pdf = html.write_pdf()
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=export_{id}.pdf'
        return response
    except URLFetchingError as e:
        logger.error(f"Error loading resources: {str(e)}")
        return f"Error loading resources: {str(e)}", 500
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return f"Error generating PDF: {str(e)}", 500

@app.route('/save/<int:id>', methods=['POST'])
def save_export(id):
    export = ExportRequest.query.get_or_404(id)
    export.status = 'saved'
    db.session.commit()
    return redirect(url_for('list_exports'))

@app.route('/get-images/<int:id>')
def get_images(id):
    try:
        request_data = ExportRequest.query.get_or_404(id)
        images = [item.image_filename for item in request_data.items if item.image_filename]
        return jsonify({'images': images})
    except Exception as e:
        logger.error(f"Error getting images: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<path:file_id>')
def serve_image(file_id):
    """Serve uploaded images from Appwrite"""
    try:
        logger.debug(f'Attempting to serve image with ID: {file_id}')
        result = storage.get_file_view(
            bucket_id=APPWRITE_BUCKET_ID,
            file_id=file_id
        )
        logger.debug(f'Appwrite response for file {file_id}: {result}')
        
        if isinstance(result, dict) and 'href' in result:
            logger.debug(f'Redirecting to Appwrite URL: {result["href"]}')
            return redirect(result['href'])
        else:
            logger.error(f'Unexpected response format from Appwrite: {result}')
            return "Image not found", 404
    except Exception as e:
        logger.error(f"Error serving image {file_id}: {str(e)}")
        return "Image not found", 404

class TemplateExportRequest:
    def __init__(self, **kwargs):
        self.waybill_number = kwargs.get('waybill_number', '')  # Empty for manual filling
        self.created_at = kwargs.get('created_at')
        self.sender_name = kwargs.get('sender_name', '')  # Empty for manual filling
        self.sender_email = kwargs.get('sender_email', '')
        self.sender_address = kwargs.get('sender_address', '')
        self.sender_business = kwargs.get('sender_business', '')
        self.sender_mobile = kwargs.get('sender_mobile', '')
        self.receiver_name = kwargs.get('receiver_name', '')
        self.receiver_email = kwargs.get('receiver_email', '')
        self.receiver_address = kwargs.get('receiver_address', '')
        self.receiver_business = kwargs.get('receiver_business', '')
        self.receiver_mobile = kwargs.get('receiver_mobile', '')
        self.destination_address = kwargs.get('destination_address', '')
        self.destination_country = kwargs.get('destination_country', '')
        self.destination_postcode = kwargs.get('destination_postcode', '')
        self.is_collection = kwargs.get('is_collection', False)  # Default to unchecked
        self.customer_group = kwargs.get('customer_group', '')
        self.order_booked_by = kwargs.get('order_booked_by', '')
        self.items = kwargs.get('items', [])

@app.route('/print-form-template')
@login_required
def print_form_template():
    logger.debug("Preparing data for print form template")
    
    # Create template object with empty values for manual filling
    export_request = TemplateExportRequest(
        waybill_number='',  # Empty for manual filling
        created_at=None,  # Set to None so date can be filled by hand
        items=[]
    )
    
    logger.debug("Created template with empty values for manual filling")
    logger.debug("Attempting to render print form template")
    
    return render_template('print_form.html', export_request=export_request)

# Add new route for printing specific export request
@app.route('/print-form/<int:id>')
def print_form(id):
    """Route to display a printable form for a specific export request."""
    try:
        request_data = ExportRequest.query.get_or_404(id)
        logger.debug(f'Accessing print form for export request {id}')
        logger.debug(f'Found export request: {request_data.waybill_number}')
        
        # Calculate totals (same as preview route)
        subtotal = sum([
            request_data.freight_pricing or 0,
            request_data.additional_charges or 0,
            request_data.pickup_charge or 0,
            request_data.handling_fees or 0,
            request_data.crating or 0,
            request_data.insurance_charge or 0
        ])
        vat = subtotal * 0.07
        total = subtotal + vat
        
        logger.debug(f'Calculated subtotal: {subtotal}, VAT: {vat}, Total: {total}')
        
        return render_template('print_form.html',
                            request=request_data,
                            subtotal=subtotal,
                            vat=vat,
                            total=total)
    except Exception as e:
        logger.error(f'Error in print form route: {str(e)}')
        raise

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return render_template('change_password.html')
        
        # Validate new password
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return render_template('change_password.html')
        
        # Validate password strength
        if len(new_password) < 8 or not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password):
            flash('Password must be at least 8 characters long and contain both letters and numbers', 'danger')
            return render_template('change_password.html')
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('Password changed successfully', 'success')
        return redirect(url_for('new_export'))
        
    return render_template('change_password.html')

@app.route('/admin/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('new_export'))
    
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/admin/reset-password/<int:user_id>', methods=['POST'])
@login_required
def reset_user_password(user_id):
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('new_export'))
    
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    
    # Validate password strength
    if len(new_password) < 8 or not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password):
        flash('Password must be at least 8 characters long and contain both letters and numbers', 'danger')
        return redirect(url_for('manage_users'))
    
    user.set_password(new_password)
    db.session.commit()
    flash(f'Password reset for user {user.username}', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('new_export'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting the last admin
    if user.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
        flash('Cannot delete the last admin user', 'danger')
        return redirect(url_for('manage_users'))
    
    # Prevent self-deletion
    if user.id == current_user.id:
        flash('Cannot delete your own account', 'danger')
        return redirect(url_for('manage_users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User {username} has been deleted', 'success')
    return redirect(url_for('manage_users'))

def acquire_lock(lock_file):
    """Acquire a file lock"""
    try:
        f = open(lock_file, 'w')
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except IOError:
        return None

def release_lock(lock_file_handle):
    """Release the file lock"""
    if lock_file_handle:
        fcntl.flock(lock_file_handle, fcntl.LOCK_UN)
        lock_file_handle.close()

def verify_db_connection():
    """Verify database connection by executing a simple query"""
    try:
        # Log the database URL (with password masked)
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        if 'postgresql://' in db_url:
            masked_url = db_url.replace(db_url.split('@')[0].split('://')[-1], '****:****')
            logger.info(f"Attempting to connect to database: {masked_url}")
        
        # Test the connection
        db.session.execute(text('SELECT 1'))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

def init_db():
    """Initialize the database and create all tables"""
    try:
        with app.app_context():
            # Verify connection first
            if not verify_db_connection():
                raise Exception("Database connection failed")
            
            # Proceed with initialization
            db.create_all()
            create_default_admin()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

def verify_database():
    """Verify database state and log detailed information"""
    try:
        with app.app_context():
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Current database tables: {tables}")
            
            # Check User table
            if 'user' in tables:
                user_count = User.query.count()
                logger.info(f"User table exists with {user_count} users")
                if user_count == 0:
                    logger.warning("User table exists but is empty")
            else:
                logger.error("User table does not exist")
                
            # Log table columns
            for table in tables:
                columns = [col['name'] for col in inspector.get_columns(table)]
                logger.debug(f"Table '{table}' columns: {columns}")
                
    except Exception as e:
        logger.error(f"Error verifying database: {str(e)}")
        raise

# After all routes are defined
def log_registered_routes():
    """Log all registered routes for debugging"""
    logger.info("Registered Routes:")
    for rule in app.url_map.iter_rules():
        logger.info(f"Route: {rule.rule}, Endpoint: {rule.endpoint}, Methods: {rule.methods}")

# Initialize database when app starts
with app.app_context():
    init_db()
    verify_database()
    log_registered_routes()

if __name__ == '__main__':
    app.run(debug=True)

@app.before_request
def log_request_info():
    logger.debug('-------------------------')
    logger.debug(f'Endpoint: {request.endpoint}')
    logger.debug(f'Method: {request.method}')
    logger.debug(f'URL: {request.url}')
    logger.debug('-------------------------') 