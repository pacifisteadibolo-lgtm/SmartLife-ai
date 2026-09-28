from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError

from modules.database import db, Preinscription, Filiere, Niveau, AnneeAcademique

preinscription_bp = Blueprint('preinscription', __name__, template_folder='../templates/preinscription')


@preinscription_bp.route('/preinscription', methods=['GET', 'POST'])
def formulaire():
    filieres = Filiere.query.filter_by(active=True).order_by(Filiere.nom).all()
    annees = AnneeAcademique.query.order_by(AnneeAcademique.libelle.desc()).all()
    annee_active = next((a for a in annees if a.active), None)

    if request.method == 'POST':
        try:
            filiere_id = int(request.form['filiere_id'])
            niveau_id = int(request.form['niveau_id'])
            annee_id = int(request.form['annee_academique_id'])
        except (KeyError, ValueError):
            flash('La filière, le niveau et l’année académique sont obligatoires.', 'error')
            return render_template('preinscription/formulaire.html', filieres=filieres, annees=annees, annee_active=annee_active)

        nom = request.form.get('nom', '').strip()
        prenom = request.form.get('prenom', '').strip()
        email = request.form.get('email', '').strip().lower()
        telephone = request.form.get('telephone', '').strip()

        if not nom or not prenom or not email or not telephone:
            flash('Nom, prénom, email et téléphone sont obligatoires.', 'error')
            return render_template('preinscription/formulaire.html', filieres=filieres, annees=annees, annee_active=annee_active)

        filiere = db.session.get(Filiere, filiere_id)
        niveau = db.session.get(Niveau, niveau_id)
        annee = db.session.get(AnneeAcademique, annee_id)
        if not filiere or not niveau or not annee or niveau.filiere_id != filiere.id or niveau.annee_academique_id != annee.id:
            flash('La combinaison filière / niveau / année est invalide.', 'error')
            return render_template('preinscription/formulaire.html', filieres=filieres, annees=annees, annee_active=annee_active)

        deja = Preinscription.query.filter(
            Preinscription.email == email,
            Preinscription.annee_academique_id == annee_id,
            Preinscription.statut.in_(['en_attente', 'acceptee'])
        ).first()
        if deja:
            flash('Une préinscription existe déjà avec cet email pour cette année.', 'error')
            return render_template('preinscription/formulaire.html', filieres=filieres, annees=annees, annee_active=annee_active)

        date_naissance = None
        if request.form.get('date_naissance'):
            try:
                date_naissance = datetime.strptime(request.form['date_naissance'], '%Y-%m-%d').date()
            except ValueError:
                flash('La date de naissance est invalide.', 'error')
                return render_template('preinscription/formulaire.html', filieres=filieres, annees=annees, annee_active=annee_active)

        db.session.add(Preinscription(
            nom=nom,
            prenom=prenom,
            email=email,
            telephone=telephone,
            date_naissance=date_naissance,
            lieu_naissance=request.form.get('lieu_naissance', '').strip() or None,
            adresse=request.form.get('adresse', '').strip() or None,
            filiere_id=filiere_id,
            niveau_id=niveau_id,
            annee_academique_id=annee_id,
        ))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Impossible d’enregistrer la préinscription. Vérifie les données.', 'error')
            return render_template('preinscription/formulaire.html', filieres=filieres, annees=annees, annee_active=annee_active)

        return redirect(url_for('preinscription.confirmation'))

    return render_template('preinscription/formulaire.html', filieres=filieres, annees=annees, annee_active=annee_active)


@preinscription_bp.route('/preinscription/confirmation')
def confirmation():
    return render_template('preinscription/confirmation.html')


@preinscription_bp.route('/preinscription/niveaux/<int:filiere_id>')
def niveaux(filiere_id):
    niveaux = Niveau.query.filter_by(filiere_id=filiere_id, active=True).order_by(Niveau.nom).all()
    return {'niveaux': [{'id': n.id, 'nom': n.nom, 'code': n.code, 'annee_academique_id': n.annee_academique_id} for n in niveaux]}
