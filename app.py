import eventlet
eventlet.monkey_patch()
# ^ DOIT être la toute première chose exécutée, avant même les imports Flask/SQLAlchemy
# ci-dessous. On avait retiré cette ligne en pensant que gunicorn s'en chargeait tout
# seul, mais dans cet environnement ce n'était pas suffisant : les verrous internes de
# SQLAlchemy (pool de connexions DB) se créaient avant la fin du patch, ce qui causait
# un crash "RuntimeError: cannot notify on un-acquired lock" sur TOUTES les pages
# utilisant la base de données (donc /dashboard/, etc.) des qu'eventlet les manipulait.

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
    # async_mode='eventlet' correspond au worker gunicorn (voir Procfile). Necessite
    # dnspython==2.3.0 (voir requirements.txt) pour qu'eventlet s'importe correctement
    # (les versions recentes de dnspython cassent le module greendns d'eventlet).
    # ping_interval/ping_timeout : valeurs par defaut de Socket.IO. Des valeurs trop
    # courtes provoquent des deconnexions en boucle des qu'une reponse met un peu plus
    # de temps, ce qui donne l'impression que les messages se perdent ou sont lents.
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet',
                       manage_session=True, ping_interval=25, ping_timeout=20)
    csrf.init_app(app)

    # Blueprints
    from modules.auth       import auth_bp
    from modules.finance    import finance_bp
    from modules.planner    import planner_bp
    from modules.dashboard  import dashboard_bp
    from modules.social     import social_bp
    from modules.ai         import ai_bp
    from modules.messagerie import messagerie_bp
    from modules.notifications import notifications_bp

    app.register_blueprint(auth_bp,       url_prefix='/auth')
    app.register_blueprint(finance_bp,    url_prefix='/finance')
    app.register_blueprint(planner_bp,    url_prefix='/planner')
    app.register_blueprint(dashboard_bp,  url_prefix='/dashboard')
    app.register_blueprint(social_bp,     url_prefix='/social')
    app.register_blueprint(ai_bp,         url_prefix='/ai')
    app.register_blueprint(messagerie_bp, url_prefix='/messagerie')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')

    # Evenements temps reel (messages prives + groupes)
    from modules.sockets import enregistrer_evenements_socket
    enregistrer_evenements_socket()

    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard.accueil'))
        return redirect(url_for('auth.login'))

    @app.route('/sw.js')
    def service_worker():
        # Servi à la racine (et non /static/sw.js) pour que sa "portée" couvre
        # TOUTE l'application, pas seulement le dossier /static/.
        from flask import send_from_directory, make_response
        resp = make_response(send_from_directory(app.static_folder, 'sw.js'))
        resp.headers['Content-Type'] = 'application/javascript'
        resp.headers['Service-Worker-Allowed'] = '/'
        return resp

    return app

app = create_app()

if __name__ == '__main__':
    # Lancement local uniquement (developpement). En production, Render
    # demarre l'app via gunicorn (voir Procfile), pas via ce bloc.
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=True, host='0.0.0.0', port=port)
