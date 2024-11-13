################################################
# Programmeerimine I
# 2024/2025 sügissemester
#
# Projekt
# Teema: SafeSend - Encrypted Messenger Application
#
# Autorid:
# Richard Mihhels, Oskar Pukk
#
# mõningane eeskuju:
# WhatsApp, Telegram disaini taoline
#
# Lisakommentaar:
# Run with: python app.py
# Requirements: flask, flask-socketio, rsa
#
##################################################

from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit
import rsa
import base64


def create_new_keypair():
    """Generate a new RSA key pair for secure messaging."""
    return rsa.newkeys(1024)


def encrypt_message(message, public_key):
    """Encrypt a message using RSA public key."""
    return rsa.encrypt(message.encode(), public_key)


def decrypt_message(encrypted_message, private_key):
    """Decrypt a message using RSA private key."""
    return rsa.decrypt(encrypted_message, private_key).decode()


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app)

# Store active user connections and their public keys
connections = {}


@app.route('/')
def index():
    """Render the main page and initialize encryption keys."""
    public_key, private_key = create_new_keypair()
    
    # Store keys in session for secure communication
    session['private_key'] = private_key.save_pkcs1('PEM').decode()
    session['public_key'] = public_key.save_pkcs1('PEM').decode()
    
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    """Handle new client connections and initiate key exchange."""
    emit('key_exchange', {'public_key': session['public_key']})


@socketio.on('send_message')
def handle_message(data):
    """Process and encrypt incoming messages before forwarding."""
    message = data['message']
    recipient_id = data.get('recipient_id')
    
    if recipient_id in connections:
        recipient_public_key = rsa.PublicKey.load_pkcs1(
            connections[recipient_id]['public_key']
        )
        encrypted_message = encrypt_message(message, recipient_public_key)
        
        # Convert encrypted message to base64 for transmission
        encoded_message = base64.b64encode(encrypted_message).decode()
        
        emit('new_message', {
            'message': encoded_message,
            'sender_id': session.get('user_id')
        }, room=recipient_id)


@socketio.on('key_exchange')
def handle_key_exchange(data):
    """Store public keys for connected users."""
    connections[session.get('user_id')] = {
        'public_key': data['public_key']
    }


def main():
    """Start the Flask application with SocketIO support."""
    socketio.run(app, debug=True)


if __name__ == '__main__':
    main()
