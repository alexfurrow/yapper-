from flask import Blueprint, request, jsonify
from backend.models.users import users
from backend.services.email_service import EmailService
from extensions import db
from functools import wraps
import os
import jwt
from datetime import datetime

auth_bp = Blueprint('auth', __name__)
email_service = EmailService()

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            user = users.verify_token(token)
            if not user:
                return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token verification error!'}), 401
        
        return f(user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/auth/register', methods=['POST'])
@rate_limit(max_requests=3, window_seconds=300)  # 3 registrations per 5 minutes
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing username, email, or password'}), 400
    
    # Validate email format
    if not users.validate_email(data['email']):
        return jsonify({'message': 'Invalid email format'}), 400
    
    # Validate password strength
    is_valid, message = users.validate_password(data['password'])
    if not is_valid:
        return jsonify({'message': message}), 400
    
    # Check if username or email already exists
    if users.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400
    
    if users.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400
    
    try:
        new_user = users(
            username=data['username'],
            email=data['email']
        )
        new_user.set_password(data['password'])
        
        # Generate email verification token
        verification_token = new_user.generate_email_verification_token()
        
        db.session.add(new_user)
        db.session.commit()
        
        # Send verification email
        email_service.send_verification_email(new_user, verification_token)
        
        return jsonify({
            'message': 'User created successfully. Please check your email to verify your account.',
            'user_id': new_user.id
        }), 201
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating user: {str(e)}'}), 500

@auth_bp.route('/auth/login', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=300)  # 5 login attempts per 5 minutes
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400
    
    user = users.query.filter_by(username=data['username']).first()
    
    if not user:
        return jsonify({'message': 'Invalid username or password'}), 401
    
    # Check if account is locked
    if user.is_account_locked():
        return jsonify({'message': 'Account is temporarily locked. Please try again later.'}), 423
    
    if not user.check_password(data['password']):
        user.increment_failed_attempts()
        return jsonify({'message': 'Invalid username or password'}), 401
    
    # Reset failed attempts on successful login
    user.reset_failed_attempts()
    
    # Check if email is verified
    if not user.email_verified:
        return jsonify({'message': 'Please verify your email address before logging in.'}), 403
    
    token = user.generate_token()
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'username': user.username,
        'user_id': user.id,
        'email_verified': user.email_verified
    }), 200

@auth_bp.route('/auth/verify-email', methods=['POST'])
def verify_email():
    data = request.get_json()
    
    if not data or not data.get('token'):
        return jsonify({'message': 'Verification token is required'}), 400
    
    user = users.query.filter_by(email_verification_token=data['token']).first()
    
    if not user:
        return jsonify({'message': 'Invalid or expired verification token'}), 400
    
    if user.verify_email_verification_token(data['token']):
        return jsonify({'message': 'Email verified successfully'}), 200
    else:
        return jsonify({'message': 'Invalid verification token'}), 400

@auth_bp.route('/auth/resend-verification', methods=['POST'])
@rate_limit(max_requests=3, window_seconds=300)  # 3 resend attempts per 5 minutes
def resend_verification():
    data = request.get_json()
    
    if not data or not data.get('email'):
        return jsonify({'message': 'Email is required'}), 400
    
    user = users.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify({'message': 'Email not found'}), 404
    
    if user.email_verified:
        return jsonify({'message': 'Email is already verified'}), 400
    
    # Generate new verification token
    verification_token = user.generate_email_verification_token()
    
    # Send verification email
    email_service.send_verification_email(user, verification_token)
    
    return jsonify({'message': 'Verification email sent successfully'}), 200

@auth_bp.route('/auth/forgot-password', methods=['POST'])
@rate_limit(max_requests=3, window_seconds=300)  # 3 password reset requests per 5 minutes
def forgot_password():
    data = request.get_json()
    
    if not data or not data.get('email'):
        return jsonify({'message': 'Email is required'}), 400
    
    user = users.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify({'message': 'If an account with this email exists, a password reset link has been sent.'}), 200
    
    # Generate password reset token
    reset_token = user.generate_password_reset_token()
    
    # Send password reset email
    email_service.send_password_reset_email(user, reset_token)
    
    return jsonify({'message': 'If an account with this email exists, a password reset link has been sent.'}), 200

@auth_bp.route('/auth/reset-password', methods=['POST'])
@rate_limit(max_requests=3, window_seconds=300)  # 3 password reset attempts per 5 minutes
def reset_password():
    data = request.get_json()
    
    if not data or not data.get('token') or not data.get('new_password'):
        return jsonify({'message': 'Token and new password are required'}), 400
    
    user = users.query.filter_by(password_reset_token=data['token']).first()
    
    if not user:
        return jsonify({'message': 'Invalid or expired reset token'}), 400
    
    if not user.verify_password_reset_token(data['token']):
        return jsonify({'message': 'Invalid or expired reset token'}), 400
    
    # Validate new password
    is_valid, message = users.validate_password(data['new_password'])
    if not is_valid:
        return jsonify({'message': message}), 400
    
    try:
        user.set_password(data['new_password'])
        user.clear_password_reset_token()
        return jsonify({'message': 'Password reset successfully'}), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': f'Error resetting password: {str(e)}'}), 500

@auth_bp.route('/auth/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.get_json()
    
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'message': 'Current password and new password are required'}), 400
    
    # Verify current password
    if not current_user.check_password(data['current_password']):
        return jsonify({'message': 'Current password is incorrect'}), 400
    
    # Validate new password
    is_valid, message = users.validate_password(data['new_password'])
    if not is_valid:
        return jsonify({'message': message}), 400
    
    try:
        current_user.set_password(data['new_password'])
        return jsonify({'message': 'Password changed successfully'}), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': f'Error changing password: {str(e)}'}), 500 