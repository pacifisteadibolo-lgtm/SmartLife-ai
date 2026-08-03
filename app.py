from flask import Flask
from flask_socketio import SocketIO
from config.settings import Config
from modules.database import db

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Blueprints
    from modules.auth    import auth_bp
    from modules.finance import finance_bp
    from modules.planner import planner_bp
    from modules.dashboard import dashboard_bp
    from modules.social  import social_bp
    from modules.ai      import ai_bp

    app.register_blueprint(auth_bp,      url_prefix='/auth')
    app.register_blueprint(finance_bp,   url_prefix='/finance')
    app.register_blueprint(planner_bp,   url_prefix='/planner')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(social_bp,    url_prefix='/social')
    app.register_blueprint(ai_bp,        url_prefix='/ai')

    return app

app = create_app()

if __name__ == '__main__':
    # Lancement local uniquement (developpement). En production, Render
    # demarre l'app via gunicorn (voir Procfile), pas via ce bloc.
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=True, host='0.0.0.0', port=port)
