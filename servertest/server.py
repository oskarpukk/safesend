import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

connected_users = {} 
username_to_sid = {}   

@app.route("/")
def index():
    return render_template("index.html")

def broadcast_user_list():
    usernames = list(username_to_sid.keys())
    socketio.emit("user_list", {"users": usernames})

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    guest_name = f"Guest{uuid.uuid4().hex[:4]}"
    connected_users[sid] = guest_name
    username_to_sid[guest_name] = sid
    broadcast_user_list()
    print("Client connected:", sid, guest_name)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in connected_users:
        username = connected_users[sid]
        del connected_users[sid]
        if username in username_to_sid:
            del username_to_sid[username]
        broadcast_user_list()
    print("Client disconnected:", sid)

@socketio.on('set_username')
def handle_set_username(data):
    sid = request.sid
    new_username = data.get("username", "").strip()
    if not new_username:
        return
    old_username = connected_users[sid]
    if old_username in username_to_sid:
        del username_to_sid[old_username]

    connected_users[sid] = new_username
    username_to_sid[new_username] = sid
    broadcast_user_list()
    print(f"User {old_username} changed username to {new_username}")

@socketio.on('chat_message')
def handle_chat_message(data):
    sid = request.sid
    username = connected_users.get(sid, "Unknown")
    message = data.get("message", "").strip()
    recipient = data.get("recipient", "Global Chat")

    if not message:
        return

    if recipient == "Global Chat":
        socketio.emit("chat_message", {"username": username, "message": message, "recipient": "Global Chat"})
        print(f"{username} (Global): {message}")
    else:
        if recipient in username_to_sid:
            target_sid = username_to_sid[recipient]
            socketio.emit("chat_message", {"username": username, "message": message, "recipient": recipient}, to=target_sid)
            socketio.emit("chat_message", {"username": username, "message": message, "recipient": recipient}, to=sid)
            print(f"{username} -> {recipient}: {message}")
        else:
            socketio.emit("chat_message", {"username": "System", "message": f"User {recipient} is not available.", "recipient": username}, to=sid)

if __name__ == "__main__":
    socketio.run(app, host="192.168.1.226", port=5000)
