from flask import session
from flask_socketio import join_room, emit, disconnect
from modules.extensions import socketio
from modules.database import db, MessagePrive, Groupe, MessageGroupe


def _room_utilisateur(user_id):
    return f"user_{user_id}"


def _room_groupe(groupe_id):
    return f"groupe_{groupe_id}"


def enregistrer_evenements_socket():
    """Appelé une fois depuis app.py après socketio.init_app(app)."""

    @socketio.on('connect')
    def on_connect():
        user_id = session.get('user_id')
        if not user_id:
            disconnect()
            return
        join_room(_room_utilisateur(user_id))

    @socketio.on('rejoindre_groupe')
    def on_rejoindre_groupe(data):
        user_id = session.get('user_id')
        if not user_id:
            return
        groupe_id = data.get('groupe_id')
        grp = db.session.get(Groupe, groupe_id)
        if grp and grp.est_membre(user_id):
            join_room(_room_groupe(groupe_id))

    @socketio.on('message_prive')
    def on_message_prive(data):
        user_id = session.get('user_id')
        if not user_id:
            return
        destinataire_id = data.get('destinataire_id')
        contenu = (data.get('contenu') or '').strip()
        if not destinataire_id or not contenu:
            return
        if len(contenu) > 4000:
            contenu = contenu[:4000]

        msg = MessagePrive(expediteur_id=user_id, destinataire_id=destinataire_id, contenu=contenu, type='texte')
        db.session.add(msg)
        db.session.commit()

        payload = msg.to_dict()
        emit('nouveau_message_prive', payload, room=_room_utilisateur(destinataire_id))
        emit('nouveau_message_prive', payload, room=_room_utilisateur(user_id))

    @socketio.on('message_groupe')
    def on_message_groupe(data):
        user_id = session.get('user_id')
        if not user_id:
            return
        groupe_id = data.get('groupe_id')
        contenu = (data.get('contenu') or '').strip()
        grp = db.session.get(Groupe, groupe_id) if groupe_id else None
        if not grp or not grp.est_membre(user_id) or not contenu:
            return
        if len(contenu) > 4000:
            contenu = contenu[:4000]

        msg = MessageGroupe(groupe_id=groupe_id, user_id=user_id, contenu=contenu, type='texte')
        db.session.add(msg)
        db.session.commit()

        emit('nouveau_message_groupe', msg.to_dict(), room=_room_groupe(groupe_id))

    @socketio.on('en_train_decrire')
    def on_typing(data):
        user_id = session.get('user_id')
        if not user_id:
            return
        cible = data.get('destinataire_id')
        groupe_id = data.get('groupe_id')
        if cible:
            emit('en_train_decrire', {'user_id': user_id}, room=_room_utilisateur(cible))
        elif groupe_id:
            emit('en_train_decrire', {'user_id': user_id, 'groupe_id': groupe_id}, room=_room_groupe(groupe_id), include_self=False)
