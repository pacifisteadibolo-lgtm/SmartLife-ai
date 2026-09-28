import json
from flask import current_app
from pywebpush import webpush, WebPushException
from modules.database import db, AbonnementPush


def envoyer_notification(user_id, titre, corps, url='/messagerie/', tag=None):
    """
    Envoie une notification push à TOUS les navigateurs abonnés de cet
    utilisateur (téléphone + PC, etc.). Fonctionne même si l'application
    n'est pas ouverte, tant que le navigateur autorise les notifications.
    Retire automatiquement les abonnements qui ne sont plus valides.

    Toute erreur est journalisée (current_app.logger) au lieu d'être
    avalée silencieusement — sans ça, impossible de diagnostiquer un
    envoi qui échoue.
    """
    private_key = current_app.config.get('VAPID_PRIVATE_KEY', '')
    public_key = current_app.config.get('VAPID_PUBLIC_KEY', '')
    if not private_key or not public_key:
        current_app.logger.warning(
            "Notification push non envoyée : VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY "
            "absentes des variables d'environnement."
        )
        return

    abonnements = AbonnementPush.query.filter_by(user_id=user_id).all()
    if not abonnements:
        current_app.logger.info(f"Aucun abonnement push pour l'utilisateur {user_id} — notification ignorée.")
        return

    payload = json.dumps({'titre': titre, 'corps': corps, 'url': url, 'tag': tag or 'message'})
    vapid_claims = {'sub': current_app.config.get('VAPID_CLAIMS_EMAIL', 'mailto:contact@example.com')}

    envoyes, echecs = 0, 0
    for abo in abonnements:
        try:
            webpush(
                subscription_info={
                    'endpoint': abo.endpoint,
                    'keys': {'p256dh': abo.p256dh, 'auth': abo.auth},
                },
                data=payload,
                vapid_private_key=private_key,
                vapid_claims=dict(vapid_claims),
            )
            envoyes += 1
        except WebPushException as e:
            statut = getattr(e.response, 'status_code', None)
            texte = getattr(e.response, 'text', str(e))
            current_app.logger.error(f"Échec notification push (abonnement {abo.id}, statut {statut}) : {texte}")
            if statut in (404, 410):
                db.session.delete(abo)  # abonnement expiré/désinstallé -> on le retire
            echecs += 1
        except Exception as e:
            current_app.logger.error(f"Erreur inattendue lors de l'envoi de la notification push : {e!r}")
            echecs += 1

    db.session.commit()
    current_app.logger.info(f"Notification push pour utilisateur {user_id} : {envoyes} envoyée(s), {echecs} échec(s).")
