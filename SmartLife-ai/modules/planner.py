from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from modules.database import db, Tache
from utils.decorators import login_required

planner_bp = Blueprint('planner', __name__, template_folder='../templates/planner')

PRIORITES_VALIDES = ['haute', 'moyenne', 'basse']


@planner_bp.route('/')
@login_required
def liste():
    filtre = request.args.get('statut', 'actives')  # actives | toutes | terminees

    query = Tache.query.filter_by(user_id=session['user_id'])
    if filtre == 'actives':
        query = query.filter(Tache.statut != 'termine')
    elif filtre == 'terminees':
        query = query.filter(Tache.statut == 'termine')

    taches = query.order_by(Tache.date_limite.asc().nulls_last()).all()
    taches = sorted(taches, key=lambda t: t.score_urgence, reverse=True) if filtre != 'terminees' else taches

    return render_template('planner/liste.html', taches=taches, filtre=filtre)


@planner_bp.route('/ajouter', methods=['POST'])
@login_required
def ajouter():
    titre = request.form.get('titre', '').strip()
    description = request.form.get('description', '').strip()
    priorite = request.form.get('priorite', 'moyenne')
    date_limite_str = request.form.get('date_limite', '').strip()

    if not titre:
        flash("Le titre de la tâche est obligatoire.", 'error')
        return redirect(url_for('planner.liste'))

    if priorite not in PRIORITES_VALIDES:
        priorite = 'moyenne'

    date_limite = None
    if date_limite_str:
        try:
            date_limite = datetime.strptime(date_limite_str, '%Y-%m-%d')
        except ValueError:
            flash("Date limite invalide.", 'error')
            return redirect(url_for('planner.liste'))

    tache = Tache(
        titre=titre,
        description=description or None,
        priorite=priorite,
        date_limite=date_limite,
        user_id=session['user_id'],
    )
    db.session.add(tache)
    db.session.commit()
    flash("Tâche ajoutée.", 'success')
    return redirect(url_for('planner.liste'))


@planner_bp.route('/<int:tache_id>/terminer', methods=['POST'])
@login_required
def terminer(tache_id):
    tache = Tache.query.filter_by(id=tache_id, user_id=session['user_id']).first_or_404()
    tache.statut = 'a_faire' if tache.statut == 'termine' else 'termine'
    db.session.commit()
    return redirect(url_for('planner.liste'))


@planner_bp.route('/<int:tache_id>/supprimer', methods=['POST'])
@login_required
def supprimer(tache_id):
    tache = Tache.query.filter_by(id=tache_id, user_id=session['user_id']).first_or_404()
    db.session.delete(tache)
    db.session.commit()
    flash("Tâche supprimée.", 'success')
    return redirect(url_for('planner.liste'))
