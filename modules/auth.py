from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from modules.database import db, Utilisateur
from datetime import datetime
import hashlib

auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')

NIVEAUX_VALIDES = ['Licence 1', 'Licence 2', 'Licence 3', 'Master 1', 'Master 2']


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        utilisateur = Utilisateur.query.filter_by(email=email).first()

        if utilisateur is None or not utilisateur.check_password(password):
            flash("Email ou mot de passe incorrect.", 'error')
            return render_template('auth/login.html'), 401

        utilisateur.last_login_at = datetime.utcnow()
        db.session.commit()
        session['user_id'] = utilisateur.id
        session['user_nom'] = utilisateur.nom
        session['user_role'] = utilisateur.role
        session['user_matricule'] = utilisateur.matricule
        flash(f"Bon retour, {utilisateur.nom} !", 'success')
        if utilisateur.must_change_password:
            return redirect(url_for('auth.changer_mot_de_passe'))
        if utilisateur.role == 'administrateur':
            return redirect(url_for('admin.accueil'))
        if utilisateur.role == 'professeur':
            return redirect(url_for('professeur.accueil'))
        return redirect(url_for('dashboard.accueil'))

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        email = request.form.get('email', '').strip().lower()
        filiere = request.form.get('filiere', '').strip()
        niveau = request.form.get('niveau', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        # -- Validation --
        if not nom or not email or not password:
            flash("Nom, email et mot de passe sont obligatoires.", 'error')
            return render_template('auth/register.html'), 400

        if len(password) < 8:
            flash("Le mot de passe doit contenir au moins 8 caractères.", 'error')
            return render_template('auth/register.html'), 400

        if password != password_confirm:
            flash("Les deux mots de passe ne correspondent pas.", 'error')
            return render_template('auth/register.html'), 400

        if niveau and niveau not in NIVEAUX_VALIDES:
            flash("Niveau invalide.", 'error')
            return render_template('auth/register.html'), 400

        if Utilisateur.query.filter_by(email=email).first() is not None:
            flash("Un compte existe déjà avec cet email.", 'error')
            return render_template('auth/register.html'), 409

        # -- Création --
        utilisateur = Utilisateur(nom=nom, email=email, filiere=filiere or None, niveau=niveau or None, role='etudiant', statut='actif')
        utilisateur.set_password(password)
        db.session.add(utilisateur)
        db.session.commit()

        session['user_id'] = utilisateur.id
        session['user_nom'] = utilisateur.nom
        session['user_role'] = utilisateur.role
        session['user_matricule'] = utilisateur.matricule
        flash("Compte créé avec succès, bienvenue !", 'success')
        return redirect(url_for('dashboard.accueil'))

    return render_template('auth/register.html')


@auth_bp.route('/changer-mot-de-passe', methods=['GET', 'POST'])
def changer_mot_de_passe():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    utilisateur = db.session.get(Utilisateur, session['user_id'])
    if not utilisateur:
        session.clear()
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        ancien = request.form.get('ancien_mot_de_passe', '')
        nouveau = request.form.get('nouveau_mot_de_passe', '')
        confirmation = request.form.get('confirmation', '')
        if not utilisateur.check_password(ancien):
            flash('Ancien mot de passe incorrect.', 'error')
        elif len(nouveau) < 8:
            flash('Le nouveau mot de passe doit contenir au moins 8 caractères.', 'error')
        elif nouveau != confirmation:
            flash('Les deux nouveaux mots de passe ne correspondent pas.', 'error')
        else:
            utilisateur.set_password(nouveau)
            utilisateur.must_change_password = False
            db.session.commit()
            flash('Mot de passe modifié avec succès.', 'success')
            if utilisateur.role == 'administrateur':
                return redirect(url_for('admin.accueil'))
            if utilisateur.role == 'professeur':
                return redirect(url_for('professeur.accueil'))
            return redirect(url_for('dashboard.accueil'))
    return render_template('auth/changer_mot_de_passe.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Tu as été déconnecté·e.", 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/activation/<token>', methods=['GET', 'POST'])
def activation(token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    utilisateur = Utilisateur.query.filter_by(activation_token_hash=token_hash).first()
    if not utilisateur or not utilisateur.activation_expires_at or utilisateur.activation_expires_at < datetime.utcnow():
        return render_template('auth/activation_invalide.html'), 410

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirmation = request.form.get('password_confirm', '')
        if len(password) < 8:
            flash('Le mot de passe doit contenir au moins 8 caractères.', 'error')
        elif password != confirmation:
            flash('Les deux mots de passe ne correspondent pas.', 'error')
        else:
            utilisateur.set_password(password)
            utilisateur.activation_token_hash = None
            utilisateur.activation_expires_at = None
            utilisateur.must_change_password = False
            db.session.commit()
            flash('Compte activé. Tu peux maintenant te connecter.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('auth/activation.html', utilisateur=utilisateur)
