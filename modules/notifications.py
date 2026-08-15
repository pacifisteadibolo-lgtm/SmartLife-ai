from flask import Blueprint, request, jsonify, session, current_app
from modules.database import db, AbonnementPush
from utils.decorators import login_required

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/cle-publique')
@login_required
def cle_publique():
    """La clé publique VAPID, nécessaire au navigateur pour s'abonner."""
    return jsonify({'cle': current_app.config.get('VAPID_PUBLIC_KEY', '')})


@notifications_bp.route('/abonner', methods=['POST'])
@login_required
def abonner():
    data = request.get_json(silent=True) or {}
    endpoint = data.get('endpoint')
    keys = data.get('keys', {})
    p256dh = keys.get('p256dh')
    auth = keys.get('auth')

    if not endpoint or not p256dh or not auth:
        return jsonify({'ok': False, 'erreur': 'Abonnement incomplet'}), 400

    existant = AbonnementPush.query.filter_by(endpoint=endpoint).first()
    if existant:
        existant.user_id = session['user_id']
        existant.p256dh = p256dh
        existant.auth = auth
    else:
        db.session.add(AbonnementPush(
            user_id=session['user_id'], endpoint=endpoint, p256dh=p256dh, auth=auth,
        ))
    db.session.commit()
    return jsonify({'ok': True})


@notifications_bp.route('/desabonner', methods=['POST'])
@login_required
def desabonner():
    data = request.get_json(silent=True) or {}
    endpoint = data.get('endpoint')
    if endpoint:
        AbonnementPush.query.filter_by(endpoint=endpoint, user_id=session['user_id']).delete()
        db.session.commit()
    return jsonify({'ok': True})
