import base64
import json
from flask import current_app
from pywebpush import webpush, WebPushException
from modules.database import db, AbonnementPush


def _cle_privee_pem():
    """La clé privée VAPID est stockée en base64 (une seule ligne) dans les
    variables d'environnement, pour éviter que Render n'abîme les retours à
    la ligne d'un vrai fichier PEM collé dans un champ texte."""
    b64 = current_app.config.get('VAPID_PRIVATE_KEY_B64', '')
    if not b64:
        return None
    return base64.b64decode(b64).decode()


def envoyer_notification(user_id, titre, corps, url='/messagerie/', tag=None):
    """
    Envoie une notification push à TOUS les navigateurs abonnés de cet
    utilisateur (téléphone + PC, etc.). Fonctionne même si l'application
    n'est pas ouverte, tant que le navigateur autorise les notifications.
    Retire automatiquement les abonnements qui ne sont plus valides
    (utilisateur ayant désinstallé/désactivé les notifications ailleurs).
    """
    private_pem = _cle_privee_pem()
    public_key = current_app.config.get('VAPID_PUBLIC_KEY', '')
    if not private_pem or not public_key:
        return  # notifications non configurées — on ignore silencieusement

    abonnements = AbonnementPush.query.filter_by(user_id=user_id).all()
    if not abonnements:
        return

    payload = json.dumps({'titre': titre, 'corps': corps, 'url': url, 'tag': tag or 'message'})
    vapid_claims = {'sub': current_app.config.get('VAPID_CLAIMS_EMAIL', 'mailto:contact@example.com')}

    for abo in abonnements:
        try:
            webpush(
                subscription_info={
                    'endpoint': abo.endpoint,
                    'keys': {'p256dh': abo.p256dh, 'auth': abo.auth},
                },
                data=payload,
                vapid_private_key=private_pem,
                vapid_claims=dict(vapid_claims),
            )
        except WebPushException as e:
            statut = getattr(e.response, 'status_code', None)
            if statut in (404, 410):
                # L'abonnement n'est plus valide (désinstallé, expiré...) -> on le retire
                db.session.delete(abo)
        except Exception:
            # Ne jamais faire planter l'envoi d'un message pour un souci de notification
            continue

    db.session.commit()
