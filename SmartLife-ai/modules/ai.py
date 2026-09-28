import requests
from flask import Blueprint, render_template, request, redirect, url_for, session
from utils.decorators import login_required

ai_bp = Blueprint('ai', __name__, template_folder='../templates/ai')

# API Google Gemini — niveau gratuit (clé à obtenir sur https://aistudio.google.com/apikey)
# On utilise l'alias "gemini-flash-latest", que Google garantit de faire pointer vers son
# modèle Flash le plus récent (avec préavis en cas de changement majeur) — plus fiable
# dans la durée qu'un nom de modèle figé, qui finit par être retiré (ex. gemini-1.5-flash).
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

SYSTEM_PROMPT = (
    "Tu es l'assistant pédagogique de SmartLife AI, une application pour étudiants. "
    "Réponds de façon claire, structurée et rigoureuse aux questions de cours (maths, "
    "sciences, informatique, méthodologie, organisation). Si tu n'es pas certain d'un "
    "fait précis (date, chiffre, référence), dis-le explicitement plutôt que d'inventer "
    "une réponse. Réponses concises mais complètes, en français sauf si on te demande "
    "une autre langue."
)

MAX_TOURS_HISTORIQUE = 12  # on ne garde que les derniers échanges, pour rester rapide


def _historique_session():
    return session.setdefault('ia_historique', [])


def _appeler_gemini(question, historique):
    from flask import current_app
    api_key = current_app.config.get('AI_API_KEY')
    if not api_key:
        return None, "L'assistant IA n'est pas encore configuré : ajoute AI_API_KEY dans tes variables d'environnement Render."

    # Reconstruit le fil de conversation au format attendu par l'API Gemini
    contents = []
    for tour in historique[-MAX_TOURS_HISTORIQUE:]:
        role = "user" if tour['role'] == 'user' else "model"
        contents.append({"role": role, "parts": [{"text": tour['contenu']}]})
    contents.append({"role": "user", "parts": [{"text": question}]})

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024},
    }

    try:
        resp = requests.post(
            GEMINI_URL,
            params={"key": api_key},
            json=payload,
            timeout=25,
        )
    except requests.exceptions.RequestException:
        return None, "L'assistant IA ne répond pas pour le moment (problème réseau). Réessaie dans un instant."

    if resp.status_code == 429:
        return None, "Trop de questions posées d'un coup (quota gratuit atteint) — réessaie dans une minute."
    if resp.status_code != 200:
        return None, f"L'assistant IA a renvoyé une erreur ({resp.status_code}). Réessaie dans un instant."

    data = resp.json()
    try:
        texte = data['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        return None, "Réponse inattendue de l'assistant IA. Réessaie ta question."

    return texte.strip(), None


@ai_bp.route('/', methods=['GET', 'POST'])
@login_required
def assistant():
    historique = _historique_session()
    erreur = None

    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        if question:
            historique.append({'role': 'user', 'contenu': question})
            reponse, erreur = _appeler_gemini(question, historique[:-1])
            if reponse:
                historique.append({'role': 'assistant', 'contenu': reponse})
            else:
                historique.pop()  # on retire la question si l'IA n'a pas pu répondre
            session.modified = True
        return redirect(url_for('ai.assistant')) if not erreur else render_template(
            'ai/assistant.html', historique=historique, erreur=erreur
        )

    return render_template('ai/assistant.html', historique=historique, erreur=erreur)


@ai_bp.route('/effacer', methods=['POST'])
@login_required
def effacer():
    session['ia_historique'] = []
    session.modified = True
    return redirect(url_for('ai.assistant'))
