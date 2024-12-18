################################################
# Programmeerimine I
# 2024/2025 sügissemester
#
# Projekt
# Teema: Serveri rakendus
#
# Autorid: 
# Oskar Pukk
# Richard Mihhels
#
# Lisakommentaar: Serveri seadistamine ja sõnumite haldamine
##################################################

from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from encryption import DiffieHellman, MessageEncryption
import logging
import socket
import os

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

# Seadista logimine
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initsialiseerime Flask ja SocketIO
app = Flask(__name__, static_folder='build', static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')  # Lisatud async_mode

# Salvesta kasutaja andmed koos nende võtmetega
users = {}  # Kasutus {sid: {'username': str, 'private_key': int, 'public_key': int, 'encryption': dict}}
username_to_sid = {}

dh = DiffieHellman()

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@socketio.on('connect')
def handle_connect():
    logger.info(f"Klient ühendas: {request.sid}")
    # Saada praegune kasutajate nimekiri äsja ühendatud kliendile
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
        # Edasta uuendatud kasutajate nimekiri
        emit('user_list', {
            'users': list(username_to_sid.keys())
        }, broadcast=True)
    logger.info(f"Klient lahkus: {request.sid}")

@socketio.on('register')
def handle_registration(data):
    sid = request.sid
    username = data.get('username', '').strip()
    private_key = int(data.get('private_key', dh.generate_private_key()))
    
    if not username:
        return {'error': 'Kasutajanimi on kohustuslik'}
        
    if username in username_to_sid:
        return {'error': 'Kasutajanimi on juba võetud'}
    
    try:
        # Generate public key
        public_key = dh.generate_public_key(private_key)
        
        # Initialize user data
        users[sid] = {
            'username': username,
            'private_key': private_key,
            'public_key': public_key,
            'encryption': {}
        }
        username_to_sid[username] = sid
        
        # Exchange keys with existing users
        for other_sid, other_user in users.items():
            if other_sid != sid:
                # Generate shared secrets for both users
                shared_secret = dh.generate_shared_secret(private_key, other_user['public_key'])
                other_shared_secret = dh.generate_shared_secret(other_user['private_key'], public_key)
                
                # Create encryption instances
                users[sid]['encryption'][other_user['username']] = MessageEncryption(shared_secret)
                users[other_sid]['encryption'][username] = MessageEncryption(other_shared_secret)
        
        # Broadcast new user to all clients
        emit('user_joined', {'username': username}, broadcast=True)
        
        # Send current user list to new user
        emit('user_list', {'users': list(username_to_sid.keys())})
        
        logger.info(f"User registered: {username}")
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
    
    try:
        if not message:
            return {'error': 'Message cannot be empty'}

        logger.info(f"Processing message from {sender['username']} to {recipient_username}")
        
        if recipient_username == "Global Chat":
            # Send to all users
            for user_sid, user_data in users.items():
                if user_sid != sid:  # Don't send to self
                    try:
                        encrypted_message = sender['encryption'][user_data['username']].encrypt(message)
                        emit('chat_message', {
                            'sender': sender['username'],
                            'message': encrypted_message,
                            'recipient': 'Global Chat',
                            'self': False
                        }, to=user_sid)
                    except Exception as e:
                        logger.error(f"Error sending to {user_data['username']}: {str(e)}")
            
            # Send confirmation to sender
            emit('chat_message', {
                'sender': sender['username'],
                'message': message,
                'recipient': 'Global Chat',
                'self': True
            }, to=sid)
            
        else:
            # Private chat
            if recipient_username in username_to_sid:
                recipient_sid = username_to_sid[recipient_username]
                
                try:
                    # Encrypt and send to recipient
                    encrypted_message = sender['encryption'][recipient_username].encrypt(message)
                    emit('chat_message', {
                        'sender': sender['username'],
                        'message': encrypted_message,
                        'recipient': recipient_username,
                        'self': False
                    }, to=recipient_sid)
                    
                    # Send confirmation to sender
                    emit('chat_message', {
                        'sender': sender['username'],
                        'message': message,
                        'recipient': recipient_username,
                        'self': True
                    }, to=sid)
                    
                except Exception as e:
                    logger.error(f"Error sending private message: {str(e)}")
                    return {'error': 'Failed to send private message'}
            else:
                return {'error': 'Recipient not found'}
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f"Message handling error: {str(e)}")
        return {'error': str(e)}

if __name__ == '__main__':
    try:
        logger.info("Käivitan serveri...")
        socketio.run(app, debug=True, host="172.25.249.164", port=3002)
    except Exception as e:
        logger.error(f"Serveri viga: {str(e)}")
