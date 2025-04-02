from flask import Blueprint, request, jsonify
from backend.models.User_Table import User_Table
from extensions import db
from functools import wraps
import os

auth_bp = Blueprint('auth', __name__)

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
        
        user = User_Table.verify_token(token)
        if not user:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    print(f"Registration attempt with data: {data}")
    
    if not data or not data.get('username') or not data.get('password'):
        print("Missing username or password")
        return jsonify({'message': 'Missing username or password'}), 400
    
    if User_Table.query.filter_by(username=data['username']).first():
        print(f"Username {data['username']} already exists")
        return jsonify({'message': 'Username already exists'}), 400
    
    try:
        new_user = User_Table(username=data['username'])
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        print(f"User {data['username']} created successfully")
        
        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        db.session.rollback()
        return jsonify({'message': f'Error creating user: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400
    
    user = User_Table.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401
    
    token = user.generate_token()
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'username': user.username,
        'user_id': user.id
    }), 200

# Export the token_required decorator so it can be used in other blueprints 