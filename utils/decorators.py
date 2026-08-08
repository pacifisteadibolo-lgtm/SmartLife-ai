from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(view):
    """Protège une route : redirige vers /auth/login si personne n'est connecté."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash("Connecte-toi pour accéder à cette page.", 'error')
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped
