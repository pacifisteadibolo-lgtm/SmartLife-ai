from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from sqlalchemy import func
from modules.database import db, Depense, Revenu, CATEGORIES_DEPENSES
from utils.decorators import login_required

finance_bp = Blueprint('finance', __name__, template_folder='../templates/finance')


@finance_bp.route('/')
@login_required
def liste():
    debut_mois = datetime.utcnow().replace(day=1)
    user_id = session['user_id']

    depenses = (
        Depense.query.filter_by(user_id=user_id)
        .filter(Depense.date >= debut_mois)
        .order_by(Depense.date.desc())
        .all()
    )
    revenus = (
        Revenu.query.filter_by(user_id=user_id)
        .filter(Revenu.date >= debut_mois)
        .order_by(Revenu.date.desc())
        .all()
    )

    total_depenses = sum(d.montant for d in depenses)
    total_revenus = sum(r.montant for r in revenus)

    par_categorie = (
        db.session.query(Depense.categorie, func.sum(Depense.montant))
        .filter(Depense.user_id == user_id, Depense.date >= debut_mois)
        .group_by(Depense.categorie)
        .order_by(func.sum(Depense.montant).desc())
        .all()
    )

    return render_template(
        'finance/liste.html',
        depenses=depenses,
        revenus=revenus,
        total_depenses=total_depenses,
        total_revenus=total_revenus,
        solde=total_revenus - total_depenses,
        par_categorie=par_categorie,
        categories=CATEGORIES_DEPENSES,
    )


@finance_bp.route('/depense/ajouter', methods=['POST'])
@login_required
def ajouter_depense():
    try:
        montant = float(request.form.get('montant', '').replace(',', '.'))
    except ValueError:
        flash("Montant invalide.", 'error')
        return redirect(url_for('finance.liste'))

    categorie = request.form.get('categorie', '')
    description = request.form.get('description', '').strip()

    if montant <= 0:
        flash("Le montant doit être positif.", 'error')
        return redirect(url_for('finance.liste'))

    if categorie not in CATEGORIES_DEPENSES:
        flash("Catégorie invalide.", 'error')
        return redirect(url_for('finance.liste'))

    depense = Depense(
        montant=montant, categorie=categorie, description=description or None,
        date=datetime.utcnow(), user_id=session['user_id'],
    )
    db.session.add(depense)
    db.session.commit()
    flash("Dépense enregistrée.", 'success')
    return redirect(url_for('finance.liste'))


@finance_bp.route('/revenu/ajouter', methods=['POST'])
@login_required
def ajouter_revenu():
    try:
        montant = float(request.form.get('montant', '').replace(',', '.'))
    except ValueError:
        flash("Montant invalide.", 'error')
        return redirect(url_for('finance.liste'))

    source = request.form.get('source', '').strip()

    if montant <= 0:
        flash("Le montant doit être positif.", 'error')
        return redirect(url_for('finance.liste'))

    if not source:
        flash("La source du revenu est obligatoire.", 'error')
        return redirect(url_for('finance.liste'))

    revenu = Revenu(montant=montant, source=source, date=datetime.utcnow(), user_id=session['user_id'])
    db.session.add(revenu)
    db.session.commit()
    flash("Revenu enregistré.", 'success')
    return redirect(url_for('finance.liste'))
