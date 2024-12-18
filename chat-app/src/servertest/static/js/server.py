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

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from encryption import DiffieHellman, MessageEncryption
import logging

# Seadista logimine
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initsialiseerime Flask ja SocketIO
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')  # Lisatud async_mode

# Salvesta kasutaja andmed koos nende võtmetega
users = {}  # Kasutus {sid: {'username': str, 'private_key': int, 'public_key': int, 'encryption': dict}}
username_to_sid = {}

dh = DiffieHellman()

@app.route('/')
def index():
    return "Server is running"  # Simple test route

@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")
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
        # Genereeri avalik võti
        public_key = dh.generate_public_key(private_key)
        
        users[sid] = {
            'username': username,
            'private_key': private_key,
            'public_key': public_key,
            'encryption': {}  # Salvestab MessageEncryption instantsid iga partneri jaoks
        }
        username_to_sid[username] = sid
        
        # Saada avalikud võtmed kõigile kasutajatele ja saa nende omad
        for other_sid, other_user in users.items():
            if other_sid != sid:
                # Genereeri jagatud saladus mõlemale kasutajale
                shared_secret = dh.generate_shared_secret(private_key, other_user['public_key'])
                users[sid]['encryption'][other_user['username']] = MessageEncryption(shared_secret)
                
                other_shared_secret = dh.generate_shared_secret(other_user['private_key'], public_key)
                users[other_sid]['encryption'][username] = MessageEncryption(other_shared_secret)
        
        # Edasta uus kasutaja
        emit('user_joined', {
            'username': username,
            'public_key': public_key
        }, broadcast=True)
        
        # Saada praegune kasutajate nimekiri uuele kasutajale
        emit('user_list', {
            'users': list(username_to_sid.keys())
        }, to=sid)
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return {'error': str(e)}

@socketio.on('chat_message')
def handle_message(data):
    """Käitleb sõnumite saatmist"""
    sid = request.sid
    if sid not in users:
        return {'error': 'Kasutaja pole registreeritud'}
        
    sender = users[sid]
    recipient_username = data.get('recipient')
    message = data.get('message', '').strip()
    
    try:
        if recipient_username == "Global Chat":
            # Üldvestluse jaoks krüpteeri sõnum igale kasutajale eraldi
            for user_sid, user_data in users.items():
                if user_sid != sid:
                    encryption = sender['encryption'].get(user_data['username'])
                    if encryption:
                        encrypted_message = encryption.encrypt(message)
                        decrypted_message = encryption.decrypt(encrypted_message)
                        
                        emit('chat_message', {
                            'sender': sender['username'],
                            'message': decrypted_message,  # Saada dekrüpteeritud sõnum
                            'recipient': 'Global Chat',
                            'self': False
                        }, to=user_sid)
            
            # Saatjale originaalsõnum
            emit('chat_message', {
                'sender': sender['username'],
                'message': message,
                'recipient': 'Global Chat',
                'self': True
            }, to=sid)
        else:
            # Privaatvestluse jaoks
            if recipient_username in username_to_sid:
                encryption = sender['encryption'].get(recipient_username)
                if encryption:
                    encrypted_message = encryption.encrypt(message)
                    decrypted_message = encryption.decrypt(encrypted_message)
                    
                    recipient_sid = username_to_sid[recipient_username]
                    emit('chat_message', {
                        'sender': sender['username'],
                        'message': decrypted_message,
                        'recipient': recipient_username,
                        'self': False
                    }, to=recipient_sid)
                    
                    emit('chat_message', {
                        'sender': sender['username'],
                        'message': message,
                        'recipient': recipient_username,
                        'self': True
                    }, to=sid)
        
        return {'success': True}
    except Exception as e:
        logger.error(f"Sõnumi saatmise viga: {str(e)}")
        return {'error': str(e)}

if __name__ == '__main__':
    try:
        logger.info("Starting server...")
        socketio.run(app, debug=True, host='0.0.0.0', port=5001)
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
