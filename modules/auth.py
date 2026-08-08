from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from modules.database import db, Utilisateur

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

        session['user_id'] = utilisateur.id
        session['user_nom'] = utilisateur.nom
        flash(f"Bon retour, {utilisateur.nom} !", 'success')
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
        utilisateur = Utilisateur(nom=nom, email=email, filiere=filiere or None, niveau=niveau or None)
        utilisateur.set_password(password)
        db.session.add(utilisateur)
        db.session.commit()

        session['user_id'] = utilisateur.id
        session['user_nom'] = utilisateur.nom
        flash("Compte créé avec succès, bienvenue !", 'success')
        return redirect(url_for('dashboard.accueil'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Tu as été déconnecté·e.", 'success')
    return redirect(url_for('auth.login'))
