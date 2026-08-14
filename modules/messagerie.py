from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from sqlalchemy import or_, func
from modules.database import (
    db, Utilisateur, MessagePrive, Groupe, GroupeMembre, MessageGroupe
)
from utils.decorators import login_required
from utils.fichiers import enregistrer_fichier, type_publication_pour
from modules.extensions import socketio

messagerie_bp = Blueprint('messagerie', __name__, template_folder='../templates/messagerie')


def _conversations_privees(user_id):
    """Liste des personnes avec qui l'utilisateur a échangé, triée par dernier message."""
    derniers = (
        db.session.query(MessagePrive)
        .filter(or_(MessagePrive.expediteur_id == user_id, MessagePrive.destinataire_id == user_id))
        .order_by(MessagePrive.date.desc())
        .all()
    )
    vues = {}
    for m in derniers:
        autre_id = m.destinataire_id if m.expediteur_id == user_id else m.expediteur_id
        if autre_id not in vues:
            non_lus = MessagePrive.query.filter_by(
                expediteur_id=autre_id, destinataire_id=user_id, lu=False
            ).count()
            vues[autre_id] = {'dernier': m, 'non_lus': non_lus}
    return vues


@messagerie_bp.route('/')
@login_required
def liste():
    user_id = session['user_id']
    conversations = _conversations_privees(user_id)

    autres_utilisateurs = {u.id: u for u in Utilisateur.query.filter(Utilisateur.id.in_(list(conversations.keys()))).all()} if conversations else {}

    groupes = (
        Groupe.query.join(GroupeMembre, Groupe.id == GroupeMembre.groupe_id)
        .filter(GroupeMembre.user_id == user_id)
        .order_by(Groupe.created_at.desc())
        .all()
    )

    tous_les_etudiants = Utilisateur.query.filter(Utilisateur.id != user_id).order_by(Utilisateur.nom).all()

    return render_template(
        'messagerie/liste.html',
        conversations=conversations,
        autres_utilisateurs=autres_utilisateurs,
        groupes=groupes,
        tous_les_etudiants=tous_les_etudiants,
    )


@messagerie_bp.route('/prive/<int:autre_id>')
@login_required
def prive(autre_id):
    user_id = session['user_id']
    autre = Utilisateur.query.get_or_404(autre_id)

    messages = (
        MessagePrive.query
        .filter(or_(
            db.and_(MessagePrive.expediteur_id == user_id, MessagePrive.destinataire_id == autre_id),
            db.and_(MessagePrive.expediteur_id == autre_id, MessagePrive.destinataire_id == user_id),
        ))
        .order_by(MessagePrive.date.asc())
        .all()
    )

    # Marquer comme lus les messages reçus
    MessagePrive.query.filter_by(expediteur_id=autre_id, destinataire_id=user_id, lu=False).update({'lu': True})
    db.session.commit()

    return render_template('messagerie/prive.html', autre=autre, messages=messages)


@messagerie_bp.route('/prive/<int:autre_id>/envoyer', methods=['POST'])
@login_required
def envoyer_prive(autre_id):
    """Fallback HTTP (sans JS) — l'envoi normal passe par SocketIO, voir modules/sockets.py"""
    user_id = session['user_id']
    Utilisateur.query.get_or_404(autre_id)
    contenu = request.form.get('contenu', '').strip()
    fichier_uploade = request.files.get('fichier')

    fichier = enregistrer_fichier(fichier_uploade, user_id) if fichier_uploade and fichier_uploade.filename else None
    if not contenu and not fichier:
        flash("Le message ne peut pas être vide.", 'error')
        return redirect(url_for('messagerie.prive', autre_id=autre_id))

    msg = MessagePrive(
        expediteur_id=user_id, destinataire_id=autre_id,
        contenu=contenu or None,
        type=type_publication_pour(fichier),
    )
    db.session.add(msg)
    db.session.flush()
    if fichier:
        fichier.msg_prive_id = msg.id
        msg.fichier_id = fichier.id
    db.session.commit()

    payload = msg.to_dict()
    socketio.emit('nouveau_message_prive', payload, room=f"user_{autre_id}")
    socketio.emit('nouveau_message_prive', payload, room=f"user_{user_id}")

    return redirect(url_for('messagerie.prive', autre_id=autre_id))


@messagerie_bp.route('/groupe/creer', methods=['POST'])
@login_required
def creer_groupe():
    user_id = session['user_id']
    nom = request.form.get('nom', '').strip()
    description = request.form.get('description', '').strip()
    membres_ids = request.form.getlist('membres')

    if not nom:
        flash("Le groupe doit avoir un nom.", 'error')
        return redirect(url_for('messagerie.liste'))

    groupe = Groupe(nom=nom, description=description, createur_id=user_id)
    db.session.add(groupe)
    db.session.flush()

    db.session.add(GroupeMembre(groupe_id=groupe.id, user_id=user_id, role='admin'))
    for mid in membres_ids:
        if str(mid) != str(user_id):
            db.session.add(GroupeMembre(groupe_id=groupe.id, user_id=int(mid), role='membre'))

    db.session.commit()
    flash(f"Groupe « {nom} » créé.", 'success')
    return redirect(url_for('messagerie.groupe', groupe_id=groupe.id))


@messagerie_bp.route('/groupe/<int:groupe_id>')
@login_required
def groupe(groupe_id):
    user_id = session['user_id']
    grp = Groupe.query.get_or_404(groupe_id)

    if not grp.est_membre(user_id):
        abort(403)

    messages = MessageGroupe.query.filter_by(groupe_id=groupe_id).order_by(MessageGroupe.date.asc()).all()
    membres = GroupeMembre.query.filter_by(groupe_id=groupe_id).all()

    return render_template('messagerie/groupe.html', groupe=grp, messages=messages, membres=membres)


@messagerie_bp.route('/groupe/<int:groupe_id>/envoyer', methods=['POST'])
@login_required
def envoyer_groupe(groupe_id):
    """Fallback HTTP (sans JS) — l'envoi normal passe par SocketIO, voir modules/sockets.py"""
    user_id = session['user_id']
    grp = Groupe.query.get_or_404(groupe_id)
    if not grp.est_membre(user_id):
        abort(403)

    contenu = request.form.get('contenu', '').strip()
    fichier_uploade = request.files.get('fichier')
    fichier = enregistrer_fichier(fichier_uploade, user_id) if fichier_uploade and fichier_uploade.filename else None

    if not contenu and not fichier:
        flash("Le message ne peut pas être vide.", 'error')
        return redirect(url_for('messagerie.groupe', groupe_id=groupe_id))

    msg = MessageGroupe(
        groupe_id=groupe_id, user_id=user_id,
        contenu=contenu or None,
        type=type_publication_pour(fichier),
    )
    db.session.add(msg)
    db.session.flush()
    if fichier:
        fichier.msg_groupe_id = msg.id
        msg.fichier_id = fichier.id
    db.session.commit()

    socketio.emit('nouveau_message_groupe', msg.to_dict(), room=f"groupe_{groupe_id}")

    return redirect(url_for('messagerie.groupe', groupe_id=groupe_id))
