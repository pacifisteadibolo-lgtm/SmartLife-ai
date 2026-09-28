from flask_socketio import SocketIO

# Instance unique partagée entre app.py et les modules (messagerie, sockets…)
# pour éviter les imports circulaires.
socketio = SocketIO()
