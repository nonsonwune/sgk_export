from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from ..models.shipment import Shipment, ShipmentItem, ShipmentStatusHistory
from ..utils.file_storage import upload_file, delete_file
from ..utils.helpers import calculate_subtotal, calculate_vat, generate_qr_code
from ..extensions import db
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import time
import uuid

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
        logger.debug("\n=== SHIPMENT SUBMISSION START ===")
        logger.debug("=== USER INFORMATION ===")
        logger.debug(f"Current User ID: {current_user.id}")
        logger.debug(f"User ID Type: {type(current_user.id)}")
        logger.debug(f"User Object: {current_user.__dict__}")
        
        form_data = request.form.to_dict()
        logger.debug("\n=== FORM DATA ===")
        logger.debug(f"Received form data: {form_data}")
        logger.debug(f"Files in request: {list(request.files.keys())}")
        
        # Create shipment object with enhanced debug logging
        logger.debug("\n=== SHIPMENT CREATION ===")
        created_by_value = current_user.id  # Remove string conversion
        logger.debug(f"Created By - Value: {created_by_value}")
        logger.debug(f"Created By - Type: {type(created_by_value)}")
        
        # Verify user exists in database
        logger.debug("\n=== USER VERIFICATION ===")
        from ..models.user import User
        user = User.query.get(current_user.id)
        if user:
            logger.debug(f"Found user in database - ID: {user.id}")
            logger.debug(f"User database ID type: {type(user.id)}")
        else:
            logger.error(f"User not found in database: {current_user.id}")
            raise ValueError("Invalid user ID")
        
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
            status='pending',
            created_by=created_by_value
        )
        
        logger.debug("\n=== SHIPMENT OBJECT CREATED ===")
        logger.debug(f"Waybill Number: {shipment.waybill_number}")
        logger.debug(f"Created By (before save): {shipment.created_by}")
        logger.debug(f"Created By Type (before save): {type(shipment.created_by)}")
        
        # Before database operations
        logger.debug("\n=== PRE-DATABASE OPERATIONS ===")
        logger.debug("Attempting to add shipment to session")
        db.session.add(shipment)
        logger.debug("Shipment added to session")
        
        try:
            logger.debug("Attempting to flush session")
            db.session.flush()
            logger.debug("Session flush successful")
            logger.debug(f"Shipment ID after flush: {shipment.id}")
            logger.debug(f"Created By after flush: {shipment.created_by}")
            logger.debug(f"Created By Type after flush: {type(shipment.created_by)}")
        except Exception as e:
            logger.error(f"Session flush error: {str(e)}")
            db.session.rollback()
            raise
        
        # Process items with enhanced logging
        logger.debug("\n=== PROCESSING ITEMS ===")
        descriptions = request.form.getlist('description[]')
        values = request.form.getlist('value[]')
        quantities = request.form.getlist('quantity[]')
        weights = request.form.getlist('weight[]')
        images = request.files.getlist('item_image[]')
        
        logger.debug(f"Number of items to process: {len(descriptions)}")
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
        
        # Final commit with verification
        logger.debug("\n=== FINAL COMMIT ===")
        try:
            db.session.commit()
            logger.debug("Database commit successful")
            
            # Verify shipment was saved correctly
            saved_shipment = Shipment.query.get(shipment.id)
            if saved_shipment:
                logger.debug(f"Verification - Found saved shipment")
                logger.debug(f"Saved shipment created_by: {saved_shipment.created_by}")
                logger.debug(f"Saved shipment created_by type: {type(saved_shipment.created_by)}")
            else:
                logger.error("Verification failed - Could not find saved shipment")
                
        except Exception as e:
            logger.error(f"Commit error: {str(e)}")
            db.session.rollback()
            raise
        
        logger.debug("=== SHIPMENT SUBMISSION COMPLETE ===\n")
        flash('Shipment created successfully!', 'success')
        return redirect(url_for('shipments.list_shipments'))
        
    except Exception as e:
        logger.error(f"Error in submit_shipment: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while creating the shipment.', 'error')
        return render_template('error.html', error=str(e)), 500

@bp.route('/view/<uuid:shipment_id>')
def view_shipment(shipment_id):
    """View a specific shipment"""
    logger.debug(f'Accessing shipment details for ID: {shipment_id}')
    try:
        # Query shipment directly with UUID
        shipment = Shipment.query.get_or_404(shipment_id)
        logger.debug(f'Found shipment with waybill: {shipment.waybill_number}')
        
        # Debug items relationship
        items = shipment.items
        logger.debug(f'Found {len(items)} items for shipment')
        logger.debug(f'Items relationship type: {type(items)}')
        logger.debug(f'Items data: {[{"id": item.id, "description": item.description} for item in items]}')
        
        # Get ordered status history
        status_history = shipment.status_history.order_by(ShipmentStatusHistory.changed_at.asc()).all()
        
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
                             status_history=status_history,
                             subtotal=subtotal,
                             vat=vat,
                             total=total)
    except Exception as e:
        logger.error(f'Error viewing shipment: {str(e)}', exc_info=True)
        flash('Error viewing shipment details', 'error')
        return redirect(url_for('shipments.list_shipments'))

@bp.route('/<uuid:shipment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_shipment(shipment_id):
    logger.debug(f'Accessing edit form for shipment {shipment_id}')
    
    # Check if user is a super user
    if not current_user.is_superuser:
        logger.warning(f'Unauthorized edit attempt by user {current_user.id}')
        flash('Access denied. Only super users can edit shipments.', 'error')
        return redirect(url_for('shipments.list_shipments'))
        
    try:
        # Query shipment directly with UUID
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
                shipment.destination_address = data['destination_address']
                shipment.destination_country = data['destination_country']
                shipment.destination_postcode = data['destination_postcode']
                
                db.session.commit()
                flash('Shipment updated successfully', 'success')
                return redirect(url_for('shipments.view_shipment', shipment_id=shipment_id))
            except Exception as e:
                db.session.rollback()
                logger.error(f'Error updating shipment: {str(e)}')
                flash('Error updating shipment', 'error')
        
        return render_template('shipments/edit.html', shipment=shipment)
    except Exception as e:
        logger.error(f'Error accessing shipment: {str(e)}')
        flash('Error accessing shipment', 'error')
        return redirect(url_for('shipments.list_shipments'))

@bp.route('/delete/<uuid:shipment_id>', methods=['POST'])
@login_required
def delete_shipment(shipment_id):
    """Delete a shipment and its associated items"""
    
    # Check if user is a super user
    if not current_user.is_superuser:
        logger.warning(f'Unauthorized delete attempt by user {current_user.id}')
        flash('Access denied. Only super users can delete shipments.', 'error')
        return redirect(url_for('shipments.list_shipments'))
        
    try:
        logger.debug(f'=== Starting Shipment Deletion Process ===')
        logger.debug(f'Shipment ID: {shipment_id}, Type: {type(shipment_id)}')
        
        # Convert shipment_id to UUID if needed
        if not isinstance(shipment_id, uuid.UUID):
            shipment_id = uuid.UUID(str(shipment_id))
            logger.debug(f'Converted shipment_id to UUID: {shipment_id}')
        
        # Get shipment with items
        shipment = Shipment.query.options(
            db.joinedload(Shipment.items)
        ).get_or_404(shipment_id)
        logger.debug(f'Found shipment with {len(shipment.items)} items')
        
        try:
            # Start a nested transaction
            with db.session.begin_nested():
                # First delete all associated items
                logger.debug('=== Deleting Associated Items ===')
                for item in shipment.items:
                    logger.debug(f'Processing item {item.id} (Type: {type(item.id)})')
                    
                    # Delete associated files if they exist
                    if item.image_file_id:
                        try:
                            delete_file(item.image_file_id)
                            logger.debug(f'Deleted file {item.image_file_id}')
                        except Exception as e:
                            logger.error(f'Error deleting file: {str(e)}')
                            # Continue with item deletion even if file deletion fails
                    
                    # Log item details before deletion
                    logger.debug(f'Item details before deletion:')
                    logger.debug(f'- ID: {item.id} (Type: {type(item.id)})')
                    logger.debug(f'- Export Request ID: {item.export_request_id} (Type: {type(item.export_request_id)})')
                    
                    # Delete the item
                    db.session.delete(item)
                    logger.debug(f'Deleted item {item.id}')
                
                logger.debug('All items deleted successfully')
                
                # Log shipment details before deletion
                logger.debug(f'Shipment details before deletion:')
                logger.debug(f'- ID: {shipment.id} (Type: {type(shipment.id)})')
                logger.debug(f'- Created By: {shipment.created_by} (Type: {type(shipment.created_by)})')
                
                # Then delete the shipment
                logger.debug('=== Deleting Shipment ===')
                db.session.delete(shipment)
                logger.debug(f'Deleted shipment {shipment.id}')
            
            # Commit the transaction
            db.session.commit()
            logger.debug('=== Deletion Process Completed Successfully ===')
            
            flash('Shipment deleted successfully', 'success')
            return redirect(url_for('shipments.list_shipments'))
            
        except Exception as nested_error:
            logger.error(f'Error in nested transaction: {str(nested_error)}', exc_info=True)
            raise
            
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting shipment: {str(e)}', exc_info=True)
        flash('Error deleting shipment. Please try again.', 'error')
        return redirect(url_for('shipments.list_shipments'))

@bp.route('/<uuid:shipment_id>/status', methods=['POST'])
@login_required
def update_status(shipment_id):
    """Update shipment status with user tracking"""
    try:
        shipment = Shipment.query.get_or_404(shipment_id)
        new_status = request.form.get('status')
        
        if new_status not in Shipment.VALID_STATUSES:
            flash('Invalid status provided.', 'error')
            return redirect(url_for('shipments.view_shipment', shipment_id=shipment_id))
            
        if shipment.update_status(new_status, current_user.id):
            flash(f'Shipment status updated to {new_status}.', 'success')
        else:
            flash('Invalid status transition.', 'error')
            
        return redirect(url_for('shipments.view_shipment', shipment_id=shipment_id))
        
    except Exception as e:
        logger.error(f"Error updating shipment status: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while updating the status.', 'error')
        return redirect(url_for('shipments.view_shipment', shipment_id=shipment_id)) 