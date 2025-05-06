from flask import Blueprint, request, jsonify
from backend.models.users import users
from extensions import db
from functools import wraps
import os
import jwt
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        print("Headers:", request.headers)  # Debug print
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            print("Auth header:", auth_header)  # Debug print
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                print("Token extracted:", token)  # Debug print
        
        if not token:
            print("No token found")  # Debug print
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            user = users.verify_token(token)
            print("User from token:", user)  # Debug print
            if not user:
                print("Token verification failed")  # Debug print
                return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            print("Exception in token verification:", str(e))  # Debug print
            return jsonify({'message': 'Token verification error!'}), 401
        
        return f(user, *args, **kwargs)
    
    return decorated

#revert in case eeded @auth_bp.route('/auth/register', methods=['POST'])
@auth_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    print(f"Registration attempt with data: {data}")
    
    if not data or not data.get('username') or not data.get('password'):
        print("Missing username or password")
        return jsonify({'message': 'Missing username or password'}), 400
    
    if users.query.filter_by(username=data['username']).first():
        print(f"Username {data['username']} already exists")
        return jsonify({'message': 'Username already exists'}), 400
    
    try:
        new_user = users(username=data['username'])
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        print(f"User {data['username']} created successfully")
        
        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        db.session.rollback()
        return jsonify({'message': f'Error creating user: {str(e)}'}), 500

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400
    
    user = users.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401
    
    token = user.generate_token()
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'username': user.username,
        'user_id': user.id
    }), 200

@staticmethod
def verify_token(token):
    try:
        payload = jwt_test.decode(
            token,
            os.environ.get('SECRET_KEY', 'dev-secret-key'),
            algorithms=['HS256']
        )
        
        # Check if token is expired
        exp_timestamp = payload.get('exp')
        if exp_timestamp:
            now = datetime.utcnow().timestamp()
            if now > exp_timestamp:
                print(f"Token expired: {datetime.fromtimestamp(exp_timestamp)} < {datetime.utcnow()}")
                return None
        
        user_id = payload.get('user_id')
        if not user_id:
            print("No user_id in token payload")
            return None
            
        user = users.query.get(user_id)
        if not user:
            print(f"No user found with id {user_id}")
            return None
            
        return user
    except jwt_test.ExpiredSignatureError:
        print("Token signature expired")
        return None
    except jwt_test.InvalidTokenError as e:
        print(f"Invalid token: {str(e)}")
        return None
    except Exception as e:
        print(f"Token verification error: {str(e)}")
        return None

# Export the token_required decorator so it can be used in other blueprints 