from flask import session
from flask_socketio import join_room, leave_room, emit, disconnect
from modules.extensions import socketio
from modules.database import db, MessagePrive, Groupe, MessageGroupe, GroupeMembre, Utilisateur
from utils.push import envoyer_notification
import secrets

# Participants actuellement dans un appel, en mémoire (un seul worker gunicorn —
# voir Procfile — donc pas de souci de cohérence entre plusieurs process).
# { call_id: { user_id: nom } }
PARTICIPANTS_APPEL = {}


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

        expediteur = db.session.get(Utilisateur, user_id)
        apercu = contenu if len(contenu) <= 80 else contenu[:77] + '…'
        envoyer_notification(
            destinataire_id,
            titre=expediteur.nom if expediteur else 'Nouveau message',
            corps=apercu,
            url=f'/messagerie/prive/{user_id}',
            tag=f'prive-{user_id}',
        )

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

        expediteur = db.session.get(Utilisateur, user_id)
        apercu = contenu if len(contenu) <= 80 else contenu[:77] + '…'
        membres = GroupeMembre.query.filter(GroupeMembre.groupe_id == groupe_id, GroupeMembre.user_id != user_id).all()
        for membre in membres:
            envoyer_notification(
                membre.user_id,
                titre=f"{expediteur.nom} · {grp.nom}" if expediteur else grp.nom,
                corps=apercu,
                url=f'/messagerie/groupe/{groupe_id}',
                tag=f'groupe-{groupe_id}',
            )

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

    # ════════════════════════════════════════════════════════════
    #  APPELS AUDIO / VIDÉO (signalisation WebRTC)
    #  Le serveur ne transporte JAMAIS le son/la vidéo — seulement les
    #  messages qui permettent aux deux navigateurs de se connecter
    #  directement entre eux (offre/réponse SDP, candidats ICE).
    # ════════════════════════════════════════════════════════════

    @socketio.on('appel_initier')
    def on_appel_initier(data):
        user_id = session.get('user_id')
        if not user_id:
            return
        appelant = db.session.get(Utilisateur, user_id)
        type_appel = data.get('type') if data.get('type') in ('audio', 'video') else 'audio'
        destinataire_id = data.get('destinataire_id')
        groupe_id = data.get('groupe_id')

        if destinataire_id:
            call_id = f"prive-{secrets.token_hex(6)}"
            emit('appel_entrant', {
                'call_id': call_id, 'type': type_appel, 'mode': 'prive',
                'appelant_id': user_id, 'appelant_nom': appelant.nom if appelant else '??',
            }, room=_room_utilisateur(destinataire_id))
            emit('appel_initie', {'call_id': call_id}, room=_room_utilisateur(user_id))

            envoyer_notification(
                destinataire_id,
                titre=f"📞 Appel {'vidéo' if type_appel == 'video' else 'audio'} de {appelant.nom if appelant else '??'}",
                corps="Touche pour répondre",
                url=f'/messagerie/prive/{user_id}',
                tag='appel',
            )

        elif groupe_id:
            grp = db.session.get(Groupe, groupe_id)
            if not grp or not grp.est_membre(user_id):
                return
            call_id = f"groupe-{groupe_id}"
            deja_dans_appel = call_id in PARTICIPANTS_APPEL and PARTICIPANTS_APPEL[call_id]
            for membre in grp.membres:
                if membre.user_id != user_id and membre.user_id not in PARTICIPANTS_APPEL.get(call_id, {}):
                    emit('appel_entrant', {
                        'call_id': call_id, 'type': type_appel, 'mode': 'groupe', 'groupe_id': groupe_id,
                        'appelant_id': user_id, 'appelant_nom': appelant.nom if appelant else '??',
                        'groupe_nom': grp.nom,
                    }, room=_room_utilisateur(membre.user_id))
                    envoyer_notification(
                        membre.user_id,
                        titre=f"📞 Appel de groupe · {grp.nom}",
                        corps=f"{appelant.nom if appelant else '??'} démarre un appel",
                        url=f'/messagerie/groupe/{groupe_id}',
                        tag='appel',
                    )
            emit('appel_initie', {'call_id': call_id, 'deja_en_cours': deja_dans_appel}, room=_room_utilisateur(user_id))

    @socketio.on('appel_rejoindre')
    def on_appel_rejoindre(data):
        """Un participant (appelant ou destinataire ayant accepté) rejoint la
        salle de signalisation de l'appel."""
        user_id = session.get('user_id')
        if not user_id:
            return
        call_id = data.get('call_id')
        if not call_id:
            return
        utilisateur = db.session.get(Utilisateur, user_id)
        nom = utilisateur.nom if utilisateur else '??'

        participants_existants = dict(PARTICIPANTS_APPEL.get(call_id, {}))

        join_room(f"appel_{call_id}")
        PARTICIPANTS_APPEL.setdefault(call_id, {})[user_id] = nom

        # On informe le nouvel arrivant de qui est déjà là (pour qu'il envoie une
        # offre WebRTC à chacun — c'est comme ça qu'on construit le maillage pour
        # les appels de groupe, et la connexion unique pour les appels privés).
        emit('appel_participants', {
            'call_id': call_id,
            'participants': [{'user_id': uid, 'nom': n} for uid, n in participants_existants.items()],
        })
        # Et on informe les participants déjà présents qu'un nouveau venu arrive.
        emit('appel_nouveau_participant', {'call_id': call_id, 'user_id': user_id, 'nom': nom},
             room=f"appel_{call_id}", include_self=False)

    @socketio.on('appel_offre')
    def on_appel_offre(data):
        user_id = session.get('user_id')
        cible = data.get('cible_user_id')
        if not user_id or not cible:
            return
        emit('appel_offre', {'call_id': data.get('call_id'), 'de_user_id': user_id, 'sdp': data.get('sdp')},
             room=_room_utilisateur(cible))

    @socketio.on('appel_reponse')
    def on_appel_reponse(data):
        user_id = session.get('user_id')
        cible = data.get('cible_user_id')
        if not user_id or not cible:
            return
        emit('appel_reponse', {'call_id': data.get('call_id'), 'de_user_id': user_id, 'sdp': data.get('sdp')},
             room=_room_utilisateur(cible))

    @socketio.on('appel_ice')
    def on_appel_ice(data):
        user_id = session.get('user_id')
        cible = data.get('cible_user_id')
        if not user_id or not cible:
            return
        emit('appel_ice', {'call_id': data.get('call_id'), 'de_user_id': user_id, 'candidate': data.get('candidate')},
             room=_room_utilisateur(cible))

    @socketio.on('appel_refuser')
    def on_appel_refuser(data):
        user_id = session.get('user_id')
        if not user_id:
            return
        appelant_id = data.get('appelant_id')
        if appelant_id:
            emit('appel_refuse', {'call_id': data.get('call_id'), 'user_id': user_id},
                 room=_room_utilisateur(appelant_id))

    @socketio.on('appel_terminer')
    def on_appel_terminer(data):
        user_id = session.get('user_id')
        call_id = data.get('call_id')
        if not user_id or not call_id:
            return
        leave_room(f"appel_{call_id}")
        if call_id in PARTICIPANTS_APPEL:
            PARTICIPANTS_APPEL[call_id].pop(user_id, None)
            if not PARTICIPANTS_APPEL[call_id]:
                del PARTICIPANTS_APPEL[call_id]
        emit('appel_participant_parti', {'call_id': call_id, 'user_id': user_id}, room=f"appel_{call_id}")

    @socketio.on('disconnect')
    def on_disconnect():
        # Si l'utilisateur ferme l'onglet en plein appel, on le retire proprement
        # de toutes les salles d'appel où il était présent.
        user_id = session.get('user_id')
        if not user_id:
            return
        for call_id in list(PARTICIPANTS_APPEL.keys()):
            if user_id in PARTICIPANTS_APPEL[call_id]:
                PARTICIPANTS_APPEL[call_id].pop(user_id, None)
                emit('appel_participant_parti', {'call_id': call_id, 'user_id': user_id}, room=f"appel_{call_id}")
                if not PARTICIPANTS_APPEL[call_id]:
                    del PARTICIPANTS_APPEL[call_id]
