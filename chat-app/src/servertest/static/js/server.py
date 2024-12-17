################################################
# Programmeerimine I
# 2024/2025 sügissemester
#
# Projekt: SafeSend - Turvaline sõnumivahetus
# Teema: Krüpteeritud vestlusrakendus
#
# Autorid:
# Richard Mihhels
# Oskar Pukk
#
# Käivitusjuhend:
# 1. Installige vajalikud paketid: pip install -r requirements.txt
# 2. Käivitage server: python server.py
# 3. Server käivitub pordil 5001
################################################

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from encryption import DiffieHellman, MessageEncryption
import logging


# Logimise seadistamine
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask ja SocketIO initsialiseerimine
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Globaalsed muutujad
users = {}  # kasutajate andmed: {sid: {'username': str, 'private_key': int, 'public_key': int}}
username_to_sid = {}  # kasutajanime ja SID seosed
dh = DiffieHellman()


@app.route('/')
def index():
    """Serveri avalehe marsruut"""
    return "Server is running"


@socketio.on('connect')
def handle_connect():
    """Käitleb kliendi ühendumist"""
    logger.info(f"Klient ühendus: {request.sid}")
    emit('user_list', {
        'users': list(username_to_sid.keys())
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Käitleb kliendi lahkumist"""
    sid = request.sid
    if sid in users:
        username = users[sid]['username']
        del username_to_sid[username]
        del users[sid]
        emit('user_left', {'username': username}, broadcast=True)
        emit('user_list', {
            'users': list(username_to_sid.keys())
        }, broadcast=True)
    logger.info(f"Klient lahkus: {request.sid}")


@socketio.on('register')
def handle_registration(data):
    """Käitleb kasutaja registreerimist
    
    Args:
        data (dict): Kasutaja registreerimise andmed
    
    Returns:
        dict: Vastus registreerimise õnnestumise kohta
    """
    sid = request.sid
    username = data.get('username', '').strip()
    private_key = int(data.get('private_key', dh.generate_private_key()))
    
    if not username:
        return {'error': 'Kasutajanimi on kohustuslik'}
    
    if username in username_to_sid:
        return {'error': 'Kasutajanimi on juba võetud'}
    
    try:
        # ... rest of the registration logic ...
        return {'success': True}
    except Exception as e:
        logger.error(f"Registreerimise viga: {str(e)}")
        return {'error': str(e)}


@socketio.on('chat_message')
def handle_message(data):
    """Käitleb sõnumite saatmist
    
    Args:
        data (dict): Sõnumi andmed
    
    Returns:
        dict: Vastus sõnumi saatmise õnnestumise kohta
    """
    sid = request.sid
    if sid not in users:
        return {'error': 'Kasutaja pole registreeritud'}
    
    sender = users[sid]
    recipient_username = data.get('recipient')
    message = data.get('message', '').strip()
    
    logger.info(f"Töötlen sõnumit kasutajalt {sender['username']} kasutajale {recipient_username}")
    
    try:
        # ... rest of the message handling logic ...
        return {'success': True}
    except Exception as e:
        logger.error(f"Sõnumi saatmise viga: {str(e)}")
        return {'error': str(e)}


if __name__ == '__main__':
    try:
        logger.info("Käivitan serveri...")
        socketio.run(app, debug=True, host='0.0.0.0', port=5001)
    except Exception as e:
        logger.error(f"Serveri viga: {str(e)}")
