from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from encryption import DiffieHellman, MessageEncryption
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask and SocketIO
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')  # Added async_mode

# Store user data with their keys
users = {}  # {sid: {'username': str, 'private_key': int, 'public_key': int, 'encryption': dict}}
username_to_sid = {}

dh = DiffieHellman()

@app.route('/')
def index():
    return "Server is running"  # Simple test route

@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")
    # Send current user list to the newly connected client
    emit('user_list', {
        'users': list(username_to_sid.keys())
    })

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in users:
        username = users[sid]['username']
        del username_to_sid[username]
        del users[sid]
        emit('user_left', {'username': username}, broadcast=True)
        # Broadcast updated user list
        emit('user_list', {
            'users': list(username_to_sid.keys())
        }, broadcast=True)
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('register')
def handle_registration(data):
    sid = request.sid
    username = data.get('username', '').strip()
    private_key = int(data.get('private_key', dh.generate_private_key()))
    
    if not username:
        return {'error': 'Username required'}
        
    if username in username_to_sid:
        return {'error': 'Username already taken'}
    
    try:
        # Generate public key
        public_key = dh.generate_public_key(private_key)
        
        users[sid] = {
            'username': username,
            'private_key': private_key,
            'public_key': public_key,
            'encryption': {}  # Will store MessageEncryption instances for each peer
        }
        username_to_sid[username] = sid
        
        # Send public keys to all users and receive theirs
        for other_sid, other_user in users.items():
            if other_sid != sid:
                # Generate shared secret for both users
                shared_secret = dh.generate_shared_secret(private_key, other_user['public_key'])
                users[sid]['encryption'][other_user['username']] = MessageEncryption(shared_secret)
                
                other_shared_secret = dh.generate_shared_secret(other_user['private_key'], public_key)
                users[other_sid]['encryption'][username] = MessageEncryption(other_shared_secret)
        
        # Broadcast new user
        emit('user_joined', {
            'username': username,
            'public_key': public_key
        }, broadcast=True)
        
        # Send current user list to new user
        emit('user_list', {
            'users': list(username_to_sid.keys())
        }, to=sid)
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return {'error': str(e)}

@socketio.on('chat_message')
def handle_message(data):
    sid = request.sid
    if sid not in users:
        return {'error': 'User not registered'}
        
    sender = users[sid]
    recipient_username = data.get('recipient')
    message = data.get('message', '').strip()
    
    logger.info(f"Processing message from {sender['username']} to {recipient_username}")
    
    try:
        if recipient_username == "Global Chat":
            # For global chat
            for user_sid, user_data in users.items():
                if user_sid != sid:
                    try:
                        # Get recipient's encryption instance for the sender
                        recipient_encryption = user_data['encryption'].get(sender['username'])
                        if recipient_encryption:
                            # Encrypt message for this specific recipient
                            encrypted_message = recipient_encryption.encrypt(message)
                            # Immediately decrypt it to verify
                            decrypted_message = recipient_encryption.decrypt(encrypted_message)
                            
                            logger.info(f"Global message: {message} -> encrypted: {encrypted_message} -> decrypted: {decrypted_message}")
                            
                            emit('chat_message', {
                                'sender': sender['username'],
                                'message': decrypted_message,  # Send decrypted message
                                'recipient': 'Global Chat',
                                'self': False
                            }, to=user_sid)
                    except Exception as e:
                        logger.error(f"Error processing message for user {user_data['username']}: {str(e)}")
            
            # Send original message back to sender
            emit('chat_message', {
                'sender': sender['username'],
                'message': message,
                'recipient': 'Global Chat',
                'self': True
            }, to=sid)
        else:
            # For private chat
            if recipient_username in username_to_sid:
                try:
                    recipient_sid = username_to_sid[recipient_username]
                    recipient_data = users[recipient_sid]
                    
                    # Get recipient's encryption instance for the sender
                    recipient_encryption = recipient_data['encryption'].get(sender['username'])
                    
                    if recipient_encryption:
                        # Encrypt and then decrypt the message
                        encrypted_message = recipient_encryption.encrypt(message)
                        decrypted_message = recipient_encryption.decrypt(encrypted_message)
                        
                        logger.info(f"Private message: {message} -> encrypted: {encrypted_message} -> decrypted: {decrypted_message}")
                        
                        # Send decrypted message to recipient
                        emit('chat_message', {
                            'sender': sender['username'],
                            'message': decrypted_message,
                            'recipient': recipient_username,
                            'self': False
                        }, to=recipient_sid)
                        
                        # Send original message back to sender
                        emit('chat_message', {
                            'sender': sender['username'],
                            'message': message,
                            'recipient': recipient_username,
                            'self': True
                        }, to=sid)
                        
                        logger.info(f"Message delivered successfully")
                except Exception as e:
                    logger.error(f"Error processing private message: {str(e)}")
        
        return {'success': True}
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return {'error': str(e)}

if __name__ == '__main__':
    try:
        logger.info("Starting server...")
        socketio.run(app, debug=True, host='0.0.0.0', port=5001)
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
