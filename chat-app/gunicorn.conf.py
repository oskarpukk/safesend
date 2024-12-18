bind = "0.0.0.0:10000"
worker_class = "flask_socketio.WebSocketWorker"
workers = 1
wsgi_app = "wsgi:app"