import os
from datetime import timedelta

class Config:
    # -- Sécurité
    SECRET_KEY = os.environ.get('SECRET_KEY', 'changez-moi-en-production')
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # -- Base de données PostgreSQL
    # Render fournit directement une DATABASE_URL (postgres://...) quand tu relies
    # la base à ton service web. On la convertit au préfixe attendu par SQLAlchemy 2.x.
    _database_url = os.environ.get('DATABASE_URL', '')
    if _database_url.startswith('postgres://'):
        _database_url = _database_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = _database_url or (
        f"postgresql://{os.environ.get('DB_USER', 'postgres')}:"
        f"{os.environ.get('DB_PASSWORD', '')}"
        f"@{os.environ.get('DB_HOST', 'localhost')}:"
        f"{os.environ.get('DB_PORT', 5432)}/"
        f"{os.environ.get('DB_NAME', 'smartlife_ai')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -- Uploads
    UPLOAD_FOLDER   = os.path.join('static', 'uploads', 'files')
    AUDIO_FOLDER    = os.path.join('static', 'uploads', 'audio')
    AVATAR_FOLDER   = os.path.join('static', 'uploads', 'avatars')
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024   # 20 Mo

    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx', 'xlsx', 'jpg', 'jpeg', 'png', 'mp4'}
    ALLOWED_AUDIO      = {'webm', 'mp3', 'ogg'}

    # -- IA (clé à renseigner dans .env)
    AI_API_KEY   = os.environ.get('AI_API_KEY', '')
    AI_API_URL   = os.environ.get('AI_API_URL', 'https://api.openai.com/v1/chat/completions')
    AI_MODEL     = os.environ.get('AI_MODEL', 'gpt-4o-mini')
