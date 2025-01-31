from flask import Flask, request, render_template, redirect, url_for, make_response, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from weasyprint import HTML, CSS
from weasyprint.urls import URLFetchingError
import os
import logging
from werkzeug.utils import secure_filename
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exports.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Add template debugging
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

db = SQLAlchemy(app)

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

def init_db():
    """Initialize the database and create all tables"""
    try:
        # Only create tables if they don't exist
        with app.app_context():
            db.create_all()
            logger.info("Database tables are ready")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

# Initialize database when the app starts
if not os.path.exists('instance/exports.db'):
    init_db()

@app.before_request
def log_request_info():
    logger.debug('-------------------------')
    logger.debug(f'Endpoint: {request.endpoint}')
    logger.debug(f'Method: {request.method}')
    logger.debug(f'URL: {request.url}')
    logger.debug('-------------------------')

@app.route('/')
@app.route('/new-export')
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
def list_exports():
    exports = ExportRequest.query.order_by(ExportRequest.created_at.desc()).all()
    return render_template('list.html', exports=exports)

@app.route('/submit', methods=['POST'])
def submit():
    logger.debug('Processing form submission')
    try:
        data = request.form
        logger.debug(f'Received form data: {data}')
        
        # Validate required fields
        required_fields = [
            'sender_name', 'sender_mobile',
            'receiver_name', 'receiver_mobile',
            'destination_address', 'destination_country', 'destination_postcode'
        ]
        for field in required_fields:
            if not data.get(field):
                error_msg = f"Please fill in the required field: {field.replace('_', ' ').title()}"
                logger.error(f"Validation error: {error_msg}")
                return render_template('form.html', error=error_msg), 400
        
        # Create new export request with draft status
        new_request = ExportRequest(
            waybill_number=ExportRequest.generate_waybill_number(),
            status='draft',
            
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
            order_booked_by=data.get('order_booked_by'),
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
                    value=float(values[i] or 0),
                    quantity=int(quantities[i] or 0),
                    weight=float(weights[i] or 0)
                )
                
                # Handle image upload
                if i < len(images) and images[i]:
                    filename = secure_filename(images[i].filename)
                    if filename:
                        logger.debug(f'Saving image for item {i+1}: {filename}')
                        images[i].save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        item.image_filename = filename
                
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
                            total=total)
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

@app.route('/uploads/<path:filename>')
def serve_image(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        logger.error(f"Error serving image: {str(e)}")
        return f"Error serving image: {str(e)}", 500

@app.route('/print-form-template')
def print_form_template():
    """Route to display an empty printable form template."""
    return render_template('print_form.html', request={
        'waybill_number': 'To be assigned',
        'status': 'new',
        'created_at': datetime.now()
    })

if __name__ == '__main__':
    app.run(debug=True) 