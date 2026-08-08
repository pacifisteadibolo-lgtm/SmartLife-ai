from flask import Blueprint, render_template, session
from datetime import datetime
from sqlalchemy import func
from modules.database import db, Utilisateur, Tache, Depense, Revenu
from utils.decorators import login_required

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates/dashboard')


@dashboard_bp.route('/')
@login_required
def accueil():
    utilisateur = db.session.get(Utilisateur, session['user_id'])

    debut_mois = datetime.utcnow().replace(day=1)

    nb_taches_en_cours = (
        Tache.query
        .filter_by(user_id=utilisateur.id)
        .filter(Tache.statut != 'termine')
        .count()
    )

    taches = (
        Tache.query
        .filter_by(user_id=utilisateur.id)
        .filter(Tache.statut != 'termine')
        .order_by(Tache.date_limite.asc().nulls_last())
        .limit(5)
        .all()
    )

    total_depenses = db.session.query(func.coalesce(func.sum(Depense.montant), 0.0)).filter(
        Depense.user_id == utilisateur.id, Depense.date >= debut_mois
    ).scalar()

    total_revenus = db.session.query(func.coalesce(func.sum(Revenu.montant), 0.0)).filter(
        Revenu.user_id == utilisateur.id, Revenu.date >= debut_mois
    ).scalar()

    return render_template(
        'dashboard/accueil.html',
        nom=utilisateur.nom,
        nb_taches_en_cours=nb_taches_en_cours,
        taches=taches,
        total_depenses=total_depenses,
        solde=total_revenus - total_depenses,
    )
