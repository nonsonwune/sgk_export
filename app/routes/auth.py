from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from ..models.user import User
from ..extensions import db
import logging

bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('shipments.new_shipment'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    logger.debug('Accessing change_password route')
    logger.debug(f'Current user: {current_user.username} (ID: {current_user.id})')
    
    if request.method == 'POST':
        logger.debug('Processing password change request')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            logger.warning(f'Invalid current password attempt for user {current_user.id}')
            flash('Current password is incorrect', 'danger')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            logger.warning(f'Password mismatch for user {current_user.id}')
            flash('New passwords do not match', 'danger')
            return render_template('change_password.html')
        
        if len(new_password) < 8:
            logger.warning(f'Password too short for user {current_user.id}')
            flash('Password must be at least 8 characters long', 'danger')
            return render_template('change_password.html')
        
        try:
            current_user.set_password(new_password)
            db.session.commit()
            logger.info(f'Password changed successfully for user {current_user.id}')
            flash('Password changed successfully', 'success')
            return redirect(url_for('shipments.new_shipment'))
        except Exception as e:
            logger.error(f'Error changing password for user {current_user.id}: {str(e)}', exc_info=True)
            db.session.rollback()
            flash('An error occurred while changing the password', 'danger')
            return render_template('change_password.html')
    
    return render_template('change_password.html') 