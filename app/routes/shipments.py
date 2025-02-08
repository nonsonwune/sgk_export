from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from ..models.shipment import Shipment, ShipmentItem
from ..utils.appwrite import upload_file, delete_file
from ..utils.helpers import calculate_subtotal, calculate_vat, generate_qr_code
from ..extensions import db
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import time

logger = logging.getLogger(__name__)

bp = Blueprint('shipments', __name__, url_prefix='/shipments')

@bp.route('/list')
@login_required
def list_shipments():
    """List all shipments"""
    try:
        logger.debug("Accessing shipments list")
        logger.debug("Checking registered endpoints")
        logger.debug(f"Available URL endpoints: {[rule.endpoint for rule in current_app.url_map.iter_rules()]}")
        logger.debug(f"Current blueprint routes: {[f'{bp.name}.{route}' for route in bp.deferred_functions]}")
        
        shipments = Shipment.query.order_by(Shipment.created_at.desc()).all()
        logger.debug(f"Found {len(shipments)} shipments")
        logger.debug("Attempting to render template: shipments/list.html")
        return render_template('shipments/list.html', shipments=shipments)
    except Exception as e:
        logger.error(f"Error in list_shipments: {str(e)}", exc_info=True)
        flash('An error occurred while loading shipments.', 'error')
        return render_template('error.html', error=str(e)), 500

@bp.route('/new')
@login_required
def new_shipment():
    """Render new shipment form"""
    try:
        logger.debug("Attempting to render new shipment template")
        logger.debug(f"Template search paths: {current_app.jinja_loader.searchpath}")
        logger.debug(f"Available templates: {os.listdir(current_app.template_folder)}")
        
        contact_data = {}
        return render_template('shipments/form.html', contact_data=contact_data)
    except Exception as e:
        logger.error(f"Error in new_shipment: {str(e)}", exc_info=True)
        flash('An error occurred while loading the new shipment form.', 'error')
        return render_template('error.html', error=str(e)), 500

@bp.route('/submit', methods=['POST'])
@login_required
def submit_shipment():
    try:
        logger.debug("Starting shipment submission")
        form_data = request.form.to_dict()
        logger.debug(f"Received form data: {form_data}")
        logger.debug(f"Files in request: {list(request.files.keys())}")
        
        # Create shipment object
        shipment = Shipment(
            waybill_number=Shipment.generate_waybill_number(),
            sender_name=form_data.get('sender_name'),
            sender_email=form_data.get('sender_email'),
            sender_address=form_data.get('sender_address'),
            sender_business=form_data.get('sender_business'),
            sender_mobile=form_data.get('sender_mobile'),
            receiver_name=form_data.get('receiver_name'),
            receiver_email=form_data.get('receiver_email'),
            receiver_address=form_data.get('receiver_address'),
            receiver_business=form_data.get('receiver_business'),
            receiver_mobile=form_data.get('receiver_mobile'),
            destination_address=form_data.get('destination_address'),
            destination_country=form_data.get('destination_country'),
            destination_postcode=form_data.get('destination_postcode'),
            freight_pricing=float(form_data.get('freight', 0)),
            additional_charges=float(form_data.get('additional', 0)),
            pickup_charge=float(form_data.get('pickup', 0)),
            handling_fees=float(form_data.get('handling', 0)),
            crating=float(form_data.get('crating', 0)),
            insurance_charge=float(form_data.get('insurance', 0)),
            is_collection=bool(form_data.get('is_collection')),
            customer_group=form_data.get('customer_group'),
            order_booked_by=form_data.get('order_booked_by'),
            sender_signature=form_data.get('sender_signature'),
            status='pending'
        )
        
        logger.debug(f"Created shipment object with waybill: {shipment.waybill_number}")
        
        # Process items
        descriptions = request.form.getlist('description[]')
        values = request.form.getlist('value[]')
        quantities = request.form.getlist('quantity[]')
        weights = request.form.getlist('weight[]')
        images = request.files.getlist('item_image[]')
        
        logger.debug(f"Processing {len(descriptions)} items")
        logger.debug(f"Number of images received: {len(images)}")
        
        for i in range(len(descriptions)):
            if descriptions[i]:  # Only create item if description exists
                try:
                    logger.debug(f"Processing item {i+1}: {descriptions[i]}")
                    item = ShipmentItem(
                        description=descriptions[i],
                        value=float(values[i]) if values[i] else 0,
                        quantity=int(quantities[i]) if quantities[i] else 0,
                        weight=float(weights[i]) if weights[i] else 0
                    )
                    
                    # Handle image upload
                    if i < len(images) and images[i].filename:
                        try:
                            logger.debug(f"Processing image for item {i+1}: {images[i].filename}")
                            logger.debug(f"File object type: {type(images[i])}")
                            logger.debug(f"File content type: {images[i].content_type}")
                            
                            filename = secure_filename(images[i].filename)
                            file_data = images[i].read()
                            logger.debug(f"Read file data of size: {len(file_data)} bytes")
                            
                            file_id = upload_file(file_data, filename)
                            if file_id:
                                logger.debug(f"Image uploaded successfully with file_id: {file_id}")
                                item.image_filename = filename
                                item.image_file_id = file_id
                                logger.debug(f"Updated item with image details - filename: {item.image_filename}, file_id: {item.image_file_id}")
                            else:
                                logger.error(f"Failed to upload image for item {i+1}")
                        except Exception as img_error:
                            logger.error(f"Error uploading image for item {i+1}: {str(img_error)}", exc_info=True)
                    
                    shipment.items.append(item)
                    logger.debug(f"Added item: {item.description} with value: {item.value}, quantity: {item.quantity}, weight: {item.weight}, image_file_id: {item.image_file_id if hasattr(item, 'image_file_id') else None}")
                except Exception as item_error:
                    logger.error(f"Error processing item {i+1}: {str(item_error)}")
                    raise
        
        # Calculate total
        shipment.total = shipment.calculated_total
        logger.debug(f"Calculated total: {shipment.total}")
        
        # After all items are processed
        db.session.add(shipment)
        logger.debug(f"Added shipment to database session")

        # Log item details before commit
        for item in shipment.items:
            logger.debug(f"Item before commit - id: {item.id}, description: {item.description}, image_file_id: {getattr(item, 'image_file_id', None)}")

        db.session.commit()
        logger.debug(f"Committed changes to database")

        # Log item details after commit
        for item in shipment.items:
            logger.debug(f"Item after commit - id: {item.id}, description: {item.description}, image_file_id: {getattr(item, 'image_file_id', None)}")

        logger.debug(f"Shipment created successfully with {len(shipment.items)} items")
        
        flash('Shipment created successfully!', 'success')
        return redirect(url_for('shipments.list_shipments'))
        
    except Exception as e:
        logger.error(f"Error in submit_shipment: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while creating the shipment.', 'error')
        return render_template('error.html', error=str(e)), 500

@bp.route('/view/<int:shipment_id>')
def view_shipment(shipment_id):
    """View a specific shipment"""
    logger.debug(f'Accessing shipment details for ID: {shipment_id}')
    try:
        shipment = Shipment.query.get_or_404(shipment_id)
        logger.debug(f'Found shipment with waybill: {shipment.waybill_number}')
        
        # Debug items relationship
        items = shipment.items
        logger.debug(f'Found {len(items)} items for shipment')
        logger.debug(f'Items relationship type: {type(items)}')
        logger.debug(f'Items data: {[{"id": item.id, "description": item.description} for item in items]}')
        
        # Calculate financial values
        logger.debug('Calculating financial values')
        subtotal = calculate_subtotal(shipment)
        vat = calculate_vat(subtotal)
        total = subtotal + vat
        logger.debug(f'Financial calculations - Subtotal: {subtotal}, VAT: {vat}, Total: {total}')
        
        # Ensure QR code exists
        if not shipment.qr_code:
            logger.debug('QR code not found, generating new one')
            qr_data = {
                'waybill': shipment.waybill_number,
                'sender': shipment.sender_name,
                'sender_mobile': shipment.sender_mobile,
                'receiver': shipment.receiver_name,
                'receiver_mobile': shipment.receiver_mobile,
                'destination': shipment.destination_address,
                'total': str(total),
                'order_booked_by': shipment.order_booked_by
            }
            logger.debug(f'QR code data prepared: {qr_data}')
            shipment.qr_code = generate_qr_code(qr_data, shipment.sender_mobile, shipment.receiver_mobile, shipment.order_booked_by)
            logger.debug('QR code generated and assigned to shipment')
            db.session.commit()
            
        logger.debug('Preparing to render template with shipment data')
        return render_template('shipments/preview.html', 
                             shipment=shipment,
                             items=items,
                             subtotal=subtotal,
                             vat=vat,
                             total=total)
    except Exception as e:
        logger.error(f'Error viewing shipment: {str(e)}', exc_info=True)
        flash('Error viewing shipment details', 'error')
        return redirect(url_for('shipments.list_shipments'))

@bp.route('/<int:shipment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_shipment(shipment_id):
    logger.debug(f'Accessing edit form for shipment {shipment_id}')
    
    # Check if user is a super user
    if not current_user.is_superuser:
        logger.warning(f'Unauthorized edit attempt by user {current_user.id}')
        flash('Access denied. Only super users can edit shipments.', 'error')
        return redirect(url_for('shipments.list_shipments'))
        
    try:
        shipment = Shipment.query.get_or_404(shipment_id)
        logger.debug(f'Found shipment with waybill: {shipment.waybill_number}')
        
        if request.method == 'POST':
            logger.debug(f'Processing edit submission for shipment {shipment_id}')
            try:
                data = request.form.to_dict()
                logger.debug(f'Received form data: {data}')
                
                # Update shipment details
                shipment.sender_name = data['sender_name']
                shipment.sender_email = data['sender_email']
                shipment.sender_mobile = data['sender_mobile']
                shipment.sender_business = data.get('sender_business')
                shipment.sender_address = data['sender_address']
                shipment.receiver_name = data['receiver_name']
                shipment.receiver_email = data['receiver_email']
                shipment.receiver_mobile = data['receiver_mobile']
                shipment.receiver_business = data.get('receiver_business')
                shipment.receiver_address = data['receiver_address']
                shipment.destination = data['destination']
                shipment.shipping_cost = float(data.get('shipping_cost', 0))
                shipment.insurance_cost = float(data.get('insurance_cost', 0))
                shipment.packaging_cost = float(data.get('packaging_cost', 0))
                shipment.other_charges = float(data.get('other_charges', 0))
                shipment.customer_group = data.get('customer_group', 'regular')
                shipment.notes = data.get('notes')
                
                logger.debug('Updated shipment details successfully')
                
                db.session.commit()
                flash('Shipment updated successfully', 'success')
                return redirect(url_for('shipments.view_shipment', shipment_id=shipment.id))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f'Error updating shipment {shipment_id}: {str(e)}', exc_info=True)
                flash('Error updating shipment', 'error')
        
        logger.debug('Rendering modify_export.html template')
        return render_template('shipments/modify_export.html', shipment=shipment)
        
    except Exception as e:
        logger.error(f'Error accessing edit form for shipment {shipment_id}: {str(e)}', exc_info=True)
        flash('Error accessing edit form', 'error')
        return redirect(url_for('shipments.list_shipments'))

@bp.route('/delete/<int:shipment_id>', methods=['POST'])
@login_required
def delete_shipment(shipment_id):
    """Delete a shipment and its associated items"""
    
    # Check if user is a super user
    if not current_user.is_superuser:
        logger.warning(f'Unauthorized delete attempt by user {current_user.id}')
        flash('Access denied. Only super users can delete shipments.', 'error')
        return redirect(url_for('shipments.list_shipments'))
        
    try:
        shipment = Shipment.query.get_or_404(shipment_id)
        
        # First delete all associated items
        for item in shipment.items:
            db.session.delete(item)
        
        # Then delete the shipment
        db.session.delete(shipment)
        db.session.commit()
        
        flash('Shipment deleted successfully', 'success')
        return redirect(url_for('shipments.list_shipments'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting shipment {shipment_id}: {str(e)}")
        flash('Error deleting shipment', 'error')
        return redirect(url_for('shipments.list_shipments'))

@bp.route('/<int:shipment_id>/status', methods=['POST'])
@login_required
def update_status(shipment_id):
    logger.debug(f'Processing status update for shipment {shipment_id}')
    try:
        shipment = Shipment.query.get_or_404(shipment_id)
        new_status = request.form.get('status')
        logger.debug(f'Current status: {shipment.status}, Requested new status: {new_status}')
        
        valid_statuses = ['pending', 'in_transit', 'delivered', 'cancelled', 'saved']
        logger.debug(f'Valid statuses: {valid_statuses}')
        
        if new_status in valid_statuses:
            logger.debug(f'Updating status from {shipment.status} to {new_status}')
            shipment.status = new_status
            db.session.commit()
            logger.debug('Status update successful')
            flash('Shipment status updated successfully', 'success')
        else:
            logger.error(f'Invalid status value received: {new_status}')
            flash('Invalid status value', 'error')
            
        return redirect(url_for('shipments.view_shipment', shipment_id=shipment_id))
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating shipment status: {str(e)}')
        flash('Error updating shipment status', 'error')
        return redirect(url_for('shipments.view_shipment', shipment_id=shipment_id)) 