from src.servertest.static.js.server import app, socketio

if __name__ == '__main__':
    socketio.run(app)