from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from ..models.shipment import Shipment
from ..extensions import db
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('contacts', __name__, url_prefix='/contacts')

@bp.route('/senders')
@login_required
def list_senders():
    logger.debug('Accessing senders list')
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 12
        
        senders = db.session.query(
            Shipment.sender_name,
            Shipment.sender_email,
            Shipment.sender_mobile,
            Shipment.sender_business,
            Shipment.sender_address,
            Shipment.customer_group
        ).distinct()
        
        total = senders.count()
        logger.debug(f'Total senders found: {total}')
        
        senders = senders.limit(per_page).offset((page - 1) * per_page).all()
        
        logger.debug(f'Found {len(senders)} senders for page {page}')
        
        contacts = [{
            'name': s.sender_name,
            'email': s.sender_email,
            'mobile': s.sender_mobile,
            'business': s.sender_business,
            'address': s.sender_address,
            'customer_group': s.customer_group
        } for s in senders]
        
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        start_index = (page - 1) * per_page + 1
        end_index = min(page * per_page, total)
        
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_page': page - 1 if has_prev else None,
            'next_page': page + 1 if has_next else None,
            'start_index': start_index,
            'end_index': end_index
        }
        
        return render_template('contacts.html', 
                             contacts=contacts, 
                             contact_type='sender',
                             pagination=pagination)
    except Exception as e:
        logger.error(f'Error in list_senders: {str(e)}')
        flash('Error loading sender list', 'error')
        return redirect(url_for('shipments.new_shipment'))

@bp.route('/receivers')
@login_required
def list_receivers():
    logger.debug('Accessing receivers list')
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 12
        
        receivers = db.session.query(
            Shipment.receiver_name,
            Shipment.receiver_email,
            Shipment.receiver_mobile,
            Shipment.receiver_business,
            Shipment.receiver_address,
            Shipment.customer_group
        ).distinct()
        
        total = receivers.count()
        logger.debug(f'Total receivers found: {total}')
        
        receivers = receivers.limit(per_page).offset((page - 1) * per_page).all()
        
        logger.debug(f'Found {len(receivers)} receivers for page {page}')
        
        contacts = [{
            'name': r.receiver_name,
            'email': r.receiver_email,
            'mobile': r.receiver_mobile,
            'business': r.receiver_business,
            'address': r.receiver_address,
            'customer_group': r.customer_group
        } for r in receivers]
        
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        start_index = (page - 1) * per_page + 1
        end_index = min(page * per_page, total)
        
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_page': page - 1 if has_prev else None,
            'next_page': page + 1 if has_next else None,
            'start_index': start_index,
            'end_index': end_index
        }
        
        return render_template('contacts.html', 
                             contacts=contacts, 
                             contact_type='receiver',
                             pagination=pagination)
    except Exception as e:
        logger.error(f'Error in list_receivers: {str(e)}')
        flash('Error loading receiver list', 'error')
        return redirect(url_for('shipments.new_shipment'))

@bp.route('/all')
@login_required
def list_all_contacts():
    logger.debug('Accessing all contacts list')
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 12
        
        senders = db.session.query(
            Shipment.sender_name.label('name'),
            Shipment.sender_email.label('email'),
            Shipment.sender_mobile.label('mobile'),
            Shipment.sender_business.label('business'),
            Shipment.sender_address.label('address'),
            Shipment.customer_group,
            db.literal('sender').label('type')
        ).distinct()
        
        receivers = db.session.query(
            Shipment.receiver_name.label('name'),
            Shipment.receiver_email.label('email'),
            Shipment.receiver_mobile.label('mobile'),
            Shipment.receiver_business.label('business'),
            Shipment.receiver_address.label('address'),
            Shipment.customer_group,
            db.literal('receiver').label('type')
        ).distinct()
        
        all_contacts = senders.union(receivers)
        
        total = all_contacts.count()
        logger.debug(f'Total contacts found: {total}')
        
        all_contacts = all_contacts.limit(per_page).offset((page - 1) * per_page).all()
        
        logger.debug(f'Found {len(all_contacts)} contacts for page {page}')
        
        contacts = [{
            'name': c.name,
            'email': c.email,
            'mobile': c.mobile,
            'business': c.business,
            'address': c.address,
            'customer_group': c.customer_group,
            'type': c.type
        } for c in all_contacts]
        
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        start_index = (page - 1) * per_page + 1
        end_index = min(page * per_page, total)
        
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_page': page - 1 if has_prev else None,
            'next_page': page + 1 if has_next else None,
            'start_index': start_index,
            'end_index': end_index
        }
        
        return render_template('contacts.html', 
                             contacts=contacts, 
                             contact_type='all',
                             pagination=pagination)
    except Exception as e:
        logger.error(f'Error in list_all_contacts: {str(e)}')
        flash('Error loading contacts list', 'error')
        return redirect(url_for('shipments.new_shipment')) 