from src.servertest.static.js.server import app, socketio

app = socketio.run(app)

if __name__ == '__main__':
    app.run()