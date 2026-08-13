from flask import Flask, session, redirect, url_for
from flask_wtf.csrf import CSRFProtect
from config.settings import Config
from modules.database import db
from modules.extensions import socketio

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", manage_session=True,
                   ping_timeout=10, ping_interval=8)
    csrf.init_app(app)

    # Blueprints
    from modules.auth       import auth_bp
    from modules.finance    import finance_bp
    from modules.planner    import planner_bp
    from modules.dashboard  import dashboard_bp
    from modules.social     import social_bp
    from modules.ai         import ai_bp
    from modules.messagerie import messagerie_bp

    app.register_blueprint(auth_bp,       url_prefix='/auth')
    app.register_blueprint(finance_bp,    url_prefix='/finance')
    app.register_blueprint(planner_bp,    url_prefix='/planner')
    app.register_blueprint(dashboard_bp,  url_prefix='/dashboard')
    app.register_blueprint(social_bp,     url_prefix='/social')
    app.register_blueprint(ai_bp,         url_prefix='/ai')
    app.register_blueprint(messagerie_bp, url_prefix='/messagerie')

    # Evenements temps reel (messages prives + groupes)
    from modules.sockets import enregistrer_evenements_socket
    enregistrer_evenements_socket()

    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard.accueil'))
        return redirect(url_for('auth.login'))

    return app

app = create_app()

if __name__ == '__main__':
    # Lancement local uniquement (developpement). En production, Render
    # demarre l'app via gunicorn (voir Procfile), pas via ce bloc.
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=True, host='0.0.0.0', port=port)
