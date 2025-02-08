from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from ..models.user import User
from ..extensions import db
import logging

bp = Blueprint('admin', __name__, url_prefix='/admin')

logger = logging.getLogger(__name__)

@bp.route('/users')
@login_required
def manage_users():
    try:
        logger.debug('Accessing manage_users route')
        logger.debug(f'Current user: {current_user.username} (ID: {current_user.id})')
        
        if not current_user.is_admin:
            logger.warning(f'Access denied for user {current_user.id} - not an admin')
            flash('Access denied', 'danger')
            return redirect(url_for('shipments.new_shipment'))
        
        # Log available endpoints after verifying admin access
        logger.debug(f'Available endpoints: {[rule.endpoint for rule in current_app.url_map.iter_rules()]}')
        
        users = User.query.all()
        logger.debug(f'Found {len(users)} users')
        return render_template('manage_users.html', users=users)
    except Exception as e:
        logger.error(f'Error in manage_users: {str(e)}', exc_info=True)
        flash('An error occurred while loading the users list.', 'error')
        return render_template('error.html', error=str(e)), 500

@bp.route('/create-user', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('shipments.new_shipment'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
        else:
            new_user = User(username=username, name=name)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('User created successfully', 'success')
            return redirect(url_for('admin.manage_users'))
            
    return render_template('create_user.html')

@bp.route('/reset-password/<int:user_id>', methods=['POST'])
@login_required
def reset_user_password(user_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('shipments.new_shipment'))
    
    user = User.query.get_or_404(user_id)
    
    if user.is_superuser and not current_user.is_superuser:
        flash('Access denied. Only Super Users can modify Super User accounts.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    new_password = request.form.get('new_password')
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters long', 'error')
        return redirect(url_for('admin.manage_users'))
    
    user.set_password(new_password)
    db.session.commit()
    flash(f'Password reset for user {user.username}', 'success')
    return redirect(url_for('admin.manage_users'))

@bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('shipments.new_shipment'))
    
    user = User.query.get_or_404(user_id)
    
    if user.is_superuser and not current_user.is_superuser:
        flash('Access denied. Only Super Users can delete Super User accounts.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    if user.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
        flash('Cannot delete the last administrator', 'error')
        return redirect(url_for('admin.manage_users'))
    
    if user.id == current_user.id:
        flash('Cannot delete your own account', 'error')
        return redirect(url_for('admin.manage_users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User {username} has been deleted', 'success')
    return redirect(url_for('admin.manage_users'))

@bp.route('/manage-admins')
@login_required
def manage_admins():
    try:
        logger.debug('Accessing manage_admins route')
        logger.debug(f'Current user: {current_user.username} (ID: {current_user.id})')
        
        if not current_user.is_superuser:
            logger.warning(f'Access denied for user {current_user.id} - not a superuser')
            flash('Access denied. Superuser privileges required.', 'error')
            return redirect(url_for('main.dashboard'))
        
        users = User.query.all()
        logger.debug(f'Found {len(users)} users')
        logger.debug(f'Admin users: {[user.username for user in users if user.is_admin]}')
        
        return render_template('manage_admins.html', users=users)
    except Exception as e:
        logger.error(f'Error in manage_admins: {str(e)}', exc_info=True)
        flash('An error occurred while loading the administrators list.', 'error')
        return render_template('error.html', error=str(e)), 500

@bp.route('/add-admin', methods=['POST'])
@login_required
def add_admin():
    if not current_user.is_superuser:
        flash('Access denied. Superuser privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')
        
        if not all([username, name, password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('admin.manage_admins'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('admin.manage_admins'))
        
        new_admin = User(
            username=username,
            name=name,
            is_admin=True,
            is_superuser=False
        )
        new_admin.set_password(password)
        
        db.session.add(new_admin)
        db.session.commit()
        
        flash('Administrator added successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error adding administrator.', 'error')
    
    return redirect(url_for('admin.manage_admins'))

@bp.route('/modify-admin/<int:user_id>', methods=['POST'])
@login_required
def modify_admin(user_id):
    if not current_user.is_superuser:
        flash('Access denied. Superuser privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        user = User.query.get_or_404(user_id)
        
        if user.is_superuser:
            flash('Cannot modify superuser accounts.', 'error')
            return redirect(url_for('admin.manage_admins'))
        
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')
        
        if not all([username, name]):
            flash('Username and name are required.', 'error')
            return redirect(url_for('admin.manage_admins'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user_id:
            flash('Username already exists.', 'error')
            return redirect(url_for('admin.manage_admins'))
        
        user.username = username
        user.name = name
        if password:
            user.set_password(password)
        
        db.session.commit()
        flash('Administrator updated successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error updating administrator.', 'error')
    
    return redirect(url_for('admin.manage_admins'))

@bp.route('/delete-admin/<int:user_id>', methods=['POST'])
@login_required
def delete_admin(user_id):
    if not current_user.is_superuser:
        flash('Access denied. Superuser privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        user = User.query.get_or_404(user_id)
        
        if user.is_superuser:
            flash('Cannot delete superuser accounts.', 'error')
            return redirect(url_for('admin.manage_admins'))
        
        if user.id == current_user.id:
            flash('Cannot delete your own account.', 'error')
            return redirect(url_for('admin.manage_admins'))
        
        db.session.delete(user)
        db.session.commit()
        flash('Administrator deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error deleting administrator.', 'error')
    
    return redirect(url_for('admin.manage_admins')) 