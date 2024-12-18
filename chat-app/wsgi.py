from gevent import monkey
monkey.patch_all()

from src.servertest.static.js.server import app, socketio

application = socketio.middleware(app)

if __name__ == '__main__':
    socketio.run(app)