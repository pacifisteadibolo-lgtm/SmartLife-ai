from flask import Blueprint, render_template, request, session, current_app, redirect, url_for
import requests
from utils.decorators import login_required

ai_bp = Blueprint('ai', __name__, template_folder='../templates/ai')

HISTORIQUE_SESSION_KEY = 'ai_historique'
MAX_TOURS_HISTORIQUE = 10


@ai_bp.route('/', methods=['GET', 'POST'])
@login_required
def assistant():
    if HISTORIQUE_SESSION_KEY not in session:
        session[HISTORIQUE_SESSION_KEY] = []

    erreur = None

    if request.method == 'POST':
        question = request.form.get('question', '').strip()

        if question:
            historique = session[HISTORIQUE_SESSION_KEY]
            historique.append({'role': 'user', 'contenu': question})

            reponse = _demander_ia(question, historique)
            if reponse is None:
                erreur = (
                    "L'assistant IA n'est pas encore configuré : ajoute AI_API_KEY "
                    "dans tes variables d'environnement Render."
                )
            else:
                historique.append({'role': 'assistant', 'contenu': reponse})

            session[HISTORIQUE_SESSION_KEY] = historique[-(MAX_TOURS_HISTORIQUE * 2):]
            session.modified = True

    return render_template(
        'ai/assistant.html',
        historique=session.get(HISTORIQUE_SESSION_KEY, []),
        erreur=erreur,
    )


@ai_bp.route('/effacer', methods=['POST'])
@login_required
def effacer():
    session[HISTORIQUE_SESSION_KEY] = []
    session.modified = True
    return redirect(url_for('ai.assistant'))


def _demander_ia(question, historique):
    """Appelle l'API IA configurée. Retourne None si la clé n'est pas configurée
    ou si l'appel échoue, pour laisser la vue afficher un message clair."""
    api_key = current_app.config.get('AI_API_KEY')
    if not api_key:
        return None

    messages = [
        {'role': 'system', 'content': (
            "Tu es l'assistant IA de SmartLife AI, une application pour étudiants. "
            "Réponds en français, de façon concise et utile."
        )}
    ]
    for tour in historique[-(MAX_TOURS_HISTORIQUE * 2):]:
        role = 'user' if tour['role'] == 'user' else 'assistant'
        messages.append({'role': role, 'content': tour['contenu']})

    try:
        resp = requests.post(
            current_app.config['AI_API_URL'],
            headers={'Authorization': f"Bearer {api_key}", 'Content-Type': 'application/json'},
            json={'model': current_app.config['AI_MODEL'], 'messages': messages},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    except Exception:
        return None
