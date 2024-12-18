import eventlet
eventlet.monkey_patch()

from src.servertest.static.js.server import app, socketio

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, 
                host='0.0.0.0',
                port=port,
                debug=False)