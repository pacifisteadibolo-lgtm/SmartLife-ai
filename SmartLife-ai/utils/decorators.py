from functools import wraps
from flask import session, redirect, url_for, flash
from modules.database import db, Utilisateur


def login_required(view):
    """Protège une route : redirige vers /auth/login si personne n'est connecté."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash("Connecte-toi pour accéder à cette page.", 'error')
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped



def admin_required(view):
    """Protège une route réservée aux administrateurs."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash("Connecte-toi pour accéder à cette page.", 'error')
            return redirect(url_for('auth.login'))
        utilisateur = db.session.get(Utilisateur, session['user_id'])
        if utilisateur is None or utilisateur.role != 'administrateur' or utilisateur.statut != 'actif':
            session.pop('user_role', None)
            flash("Accès réservé à l'administration.", 'error')
            return redirect(url_for('dashboard.accueil'))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    """Protège une route contre les rôles non autorisés."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                flash("Connecte-toi pour accéder à cette page.", 'error')
                return redirect(url_for('auth.login'))
            utilisateur = db.session.get(Utilisateur, session['user_id'])
            if utilisateur is None or utilisateur.statut != 'actif' or utilisateur.role not in roles:
                flash("Tu n’as pas les droits nécessaires.", 'error')
                return redirect(url_for('dashboard.accueil'))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def professeur_required(view):
    """Protège une route réservée aux professeurs actifs."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash("Connecte-toi pour accéder à cette page.", 'error')
            return redirect(url_for('auth.login'))
        utilisateur = db.session.get(Utilisateur, session['user_id'])
        if utilisateur is None or utilisateur.role != 'professeur' or utilisateur.statut != 'actif':
            flash("Accès réservé aux professeurs.", 'error')
            return redirect(url_for('dashboard.accueil'))
        return view(*args, **kwargs)
    return wrapped
