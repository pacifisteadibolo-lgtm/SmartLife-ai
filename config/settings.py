import os
from datetime import timedelta


class Config:
    # -- Sécurité
    SECRET_KEY = os.environ.get(
        'SECRET_KEY',
        'changez-moi-en-production'
    )

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Render définit automatiquement RENDER=true sur ses services.
    _EN_PRODUCTION = os.environ.get('RENDER') is not None

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = _EN_PRODUCTION

    if _EN_PRODUCTION and SECRET_KEY == 'changez-moi-en-production':
        import warnings

        warnings.warn(
            "SECRET_KEY par défaut utilisée en production ! "
            "Ajoute une vraie valeur aléatoire dans les variables "
            "d'environnement Render.",
            RuntimeWarning,
        )

    # -- Base de données PostgreSQL
    _database_url = os.environ.get('DATABASE_URL', '')

    if _database_url.startswith('postgres://'):
        _database_url = _database_url.replace(
            'postgres://',
            'postgresql://',
            1
        )

    if _database_url.startswith('postgresql://'):
        _database_url = _database_url.replace(
            'postgresql://',
            'postgresql+psycopg2://',
            1
        )

    SQLALCHEMY_DATABASE_URI = _database_url or (
        f"postgresql+psycopg2://{os.environ.get('DB_USER', 'postgres')}:"
        f"{os.environ.get('DB_PASSWORD', '')}"
        f"@{os.environ.get('DB_HOST', 'localhost')}:"
        f"{os.environ.get('DB_PORT', 5432)}/"
        f"{os.environ.get('DB_NAME', 'smartlife_ai')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -- Uploads
    UPLOAD_FOLDER = os.path.join(
        'static',
        'uploads',
        'files'
    )

    AUDIO_FOLDER = os.path.join(
        'static',
        'uploads',
        'audio'
    )

    AVATAR_FOLDER = os.path.join(
        'static',
        'uploads',
        'avatars'
    )

    MAX_CONTENT_LENGTH = 20 * 1024 * 1024
