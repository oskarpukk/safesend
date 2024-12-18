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
from encryption import DiffieHellmanAlg, MessageEncryption
import logging
import socket
import os

# hostname = socket.gethostname()
# local_ip = socket.gethostbyname(hostname)

# Seadista logimine
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initsialiseerime Flask ja SocketIO
app = Flask(__name__, static_folder='build', static_url_path='')
CORS(app, origins=["https://your-vercel-app.vercel.app"])
socketio = SocketIO(app, 
                   cors_allowed_origins=["https://your-vercel-app.vercel.app"],
                   async_mode='eventlet')

port = int(os.environ.get("PORT", 3000))

# Salvesta kasutaja andmed koos nende võtmetega
all_users = {}  # {sid: {'username': str, 'private_key': int, 'public_key': int, 'encryption': {username: MessageEncryption()}}}
username_to_sid = {}

dh = DiffieHellmanAlg()

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@socketio.on('connect')
def handle_connect():
    logger.info(f"Klient ühendas: {request.sid}")
    # Saada praegune kasutajate nimekiri äsja ühendatud kliendile
    emit('user_list', {
        'all_users': list(username_to_sid.keys())
    })

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in all_users:
        username = all_users[sid]['username']
        del username_to_sid[username]
        del all_users[sid]
        emit('user_left', {'username': username}, broadcast=True)
        # Edasta uuendatud kasutajate nimekiri
        emit('user_list', {
            'all_users': list(username_to_sid.keys())
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
        all_users[sid] = {
            'username': username,
            'private_key': private_key,
            'public_key': public_key,
            'encryption': {}
        }
        username_to_sid[username] = sid
        
        # Loo krüpteerimise objektid kõigi olemasolevate kasutajatega
        for other_sid, other_user in all_users.items():
            if other_sid != sid:
                # Generate shared secrets for both all_users
                shared_secret = dh.generate_shared_secret(private_key, other_user['public_key'])
                other_shared_secret = dh.generate_shared_secret(other_user['private_key'], public_key)
                
                # Create encryption instances
                all_users[sid]['encryption'][other_user['username']] = MessageEncryption(shared_secret)
                all_users[other_sid]['encryption'][username] = MessageEncryption(other_shared_secret)
        
        # Broadcast new user to all clients
        emit('user_joined', {'username': username}, broadcast=True)
        
        # Send current user list to new user
        emit('user_list', {'all_users': list(username_to_sid.keys())}, to=sid)
        
        # Saada kliendile tema enda public_key ja teiste kasutajate public_key-d
        other_all_users_info = {}
        for uname, osid in username_to_sid.items():
            if uname != username:
                other_all_users_info[uname] = all_users[osid]['public_key']
        
        logger.info(f"User registered: {username}")
        return {
            'success': True,
            'your_public_key': public_key,
            'others_public_keys': other_all_users_info,
            'P': dh.P,
            'G': dh.G
        }
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return {'error': str(e)}

@socketio.on('chat_message')
def handle_message(data):
    sid = request.sid
    if sid not in all_users:
        return {'error': 'User not registered'}
        
    sender = all_users[sid]
    recipient_username = data.get('recipient')
    message = data.get('message', '').strip()
    
    try:
        if not message:
            return {'error': 'Message cannot be empty'}

        logger.info(f"Processing message from {sender['username']} to {recipient_username}")
        
        if recipient_username == "Global Chat":
            # Send to all all_users
            for user_sid, user_data in all_users.items():
                if user_sid != sid:  # Don't send to self
                    try:
                        # Encrypt message for recipient
                        encrypted_message = sender['encryption'][user_data['username']].encrypt(message)
                        print(f"Encrypted message for {recipient_username}: {encrypted_message}")
                        # Decrypt it using recipient's encryption instance
                        decrypted_message = user_data['encryption'][sender['username']].decrypt(encrypted_message)
                        emit('chat_message', {
                            'sender': sender['username'],
                            'message': decrypted_message,
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
                    # Encrypt message for recipient
                    encrypted_message = sender['encryption'][recipient_username].encrypt(message)
                    print(f"Encrypted message for {recipient_username}: {encrypted_message}")
                    # Decrypt before sending to recipient
                    decrypted_message = all_users[recipient_sid]['encryption'][sender['username']].decrypt(encrypted_message)
                    
                    emit('chat_message', {
                        'sender': sender['username'],
                        'message': decrypted_message,  # Send decrypted message
                        'recipient': recipient_username,
                        'self': False
                    }, to=recipient_sid)
                    
                    # Send confirmation to sender (unencrypted)
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
        socketio.run(app, debug=True, host="172.20.10.8", port=port)
    except Exception as e:
        logger.error(f"Serveri viga: {str(e)}")