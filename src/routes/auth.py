from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from jose import jwt as pyjwt
from datetime import datetime, timedelta
from functools import wraps
from src.models.gym import db, GymOwner, GymClient

auth_bp = Blueprint('auth', __name__)

def token_required(user_type='both'):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                try:
                    token = auth_header.split(" ")[1]  # Bearer <token>
                except IndexError:
                    return jsonify({'message': 'Token format invalid'}), 401
            
            if not token:
                return jsonify({'message': 'Token is missing'}), 401
            
            try:
                data = pyjwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
                
                if user_type == 'owner' or (user_type == 'both' and data.get('user_type') == 'owner'):
                    current_user = GymOwner.query.filter_by(id=data['user_id']).first()
                elif user_type == 'client' or (user_type == 'both' and data.get('user_type') == 'client'):
                    current_user = GymClient.query.filter_by(id=data['user_id']).first()
                else:
                    return jsonify({'message': 'Invalid user type'}), 401
                
                if not current_user:
                    return jsonify({'message': 'User not found'}), 401
                    
            except pyjwt.ExpiredSignatureError:
                return jsonify({'message': 'Token has expired'}), 401
            except pyjwt.InvalidTokenError:
                return jsonify({'message': 'Token is invalid'}), 401
            
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator

@auth_bp.route('/register/owner', methods=['POST'])
def register_owner():
    try:
        data = request.get_json()
        print("Register Owner Data Received:", data)  # Debug log
        
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            print("Missing required fields")  # Debug log
            return jsonify({'message': 'Username, email, and password are required'}), 400
        
        # Check if user already exists
        if GymOwner.query.filter_by(username=data['username']).first():
            print("Username already exists")  # Debug log
            return jsonify({'message': 'Username already exists'}), 400
        
        if GymOwner.query.filter_by(email=data['email']).first():
            print("Email already exists")  # Debug log
            return jsonify({'message': 'Email already exists'}), 400
        
        # Create new gym owner
        hashed_password = generate_password_hash(data['password'])
        new_owner = GymOwner(
            username=data['username'],
            email=data['email'],
            password_hash=hashed_password
        )
        
        db.session.add(new_owner)
        db.session.commit()
        
        print("Gym owner registered successfully:", new_owner)  # Debug log
        
        return jsonify({
            'message': 'Gym owner registered successfully',
            'user': new_owner.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print("Registration failed:", str(e))  # Debug log
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/register/client', methods=['POST'])
def register_client():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Username, email, and password are required'}), 400
        
        # Check if user already exists
        if GymClient.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'Username already exists'}), 400
        
        if GymClient.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 400
        
        # Create new gym client
        hashed_password = generate_password_hash(data['password'])
        new_client = GymClient(
            username=data['username'],
            email=data['email'],
            password_hash=hashed_password
        )
        
        db.session.add(new_client)
        db.session.commit()
        
        return jsonify({
            'message': 'Gym client registered successfully',
            'user': new_client.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/login/owner', methods=['POST'])
def login_owner():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Username and password are required'}), 400
        
        owner = GymOwner.query.filter_by(username=data['username']).first()
        
        if owner and check_password_hash(owner.password_hash, data['password']):
            token = pyjwt.encode({
                'user_id': owner.id,
                'user_type': 'owner',
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': owner.to_dict()
            }), 200
        
        return jsonify({'message': 'Invalid credentials'}), 401
        
    except Exception as e:
        return jsonify({'message': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/login/client', methods=['POST'])
def login_client():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Username and password are required'}), 400
        
        client = GymClient.query.filter_by(username=data['username']).first()
        
        if client and check_password_hash(client.password_hash, data['password']):
            token = pyjwt.encode({
                'user_id': client.id,
                'user_type': 'client',
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': client.to_dict()
            }), 200
        
        return jsonify({'message': 'Invalid credentials'}), 401
        
    except Exception as e:
        return jsonify({'message': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    try:
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'Token format invalid'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        data = pyjwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        
        if data.get('user_type') == 'owner':
            user = GymOwner.query.filter_by(id=data['user_id']).first()
        elif data.get('user_type') == 'client':
            user = GymClient.query.filter_by(id=data['user_id']).first()
        else:
            return jsonify({'message': 'Invalid user type'}), 401
        
        if not user:
            return jsonify({'message': 'User not found'}), 401
        
        return jsonify({
            'valid': True,
            'user': user.to_dict(),
            'user_type': data.get('user_type')
        }), 200
        
    except pyjwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'message': 'Token has expired'}), 401
    except pyjwt.InvalidTokenError:
        return jsonify({'valid': False, 'message': 'Token is invalid'}), 401
    except Exception as e:
        return jsonify({'valid': False, 'message': f'Verification failed: {str(e)}'}), 500

