import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from modules.database import db, Fichier

EXTENSIONS_PHOTO = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
EXTENSIONS_VIDEO = {'mp4', 'mov', 'webm'}
EXTENSIONS_DOC   = {'pdf', 'docx', 'pptx', 'xlsx', 'txt', 'zip'}

TOUTES_EXTENSIONS = EXTENSIONS_PHOTO | EXTENSIONS_VIDEO | EXTENSIONS_DOC


def extension_autorisee(nom_fichier):
    return '.' in nom_fichier and nom_fichier.rsplit('.', 1)[1].lower() in TOUTES_EXTENSIONS


def deviner_mimetype(extension, mimetype_navigateur):
    """Le mimetype envoyé par le navigateur est parfois vide/faux -> on le déduit de l'extension en secours."""
    if mimetype_navigateur:
        return mimetype_navigateur
    if extension in EXTENSIONS_PHOTO:
        return f'image/{extension}'
    if extension in EXTENSIONS_VIDEO:
        return f'video/{extension}'
    return 'application/octet-stream'


def enregistrer_fichier(file_storage, user_id, pub_id=None):
    """
    Sauvegarde un fichier uploadé (Werkzeug FileStorage) sur le disque et crée
    l'enregistrement Fichier correspondant (ajouté à la session, PAS commité —
    l'appelant doit faire db.session.commit() après avoir lié le fichier à
    une publication / un message).
    Retourne l'objet Fichier, ou None si le fichier est invalide.
    """
    if not file_storage or not file_storage.filename:
        return None

    nom_original = secure_filename(file_storage.filename)
    if not extension_autorisee(nom_original):
        return None

    extension = nom_original.rsplit('.', 1)[1].lower()
    nom_unique = f"{uuid.uuid4().hex}.{extension}"

    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    chemin_disque = os.path.join(upload_folder, nom_unique)
    file_storage.save(chemin_disque)

    taille = os.path.getsize(chemin_disque)
    mimetype = deviner_mimetype(extension, file_storage.mimetype)

    # Chemin web (relatif à /static) pour affichage direct dans les templates
    chemin_web = chemin_disque.replace('\\', '/')
    if not chemin_web.startswith('static/'):
        chemin_web = 'static/' + chemin_web.split('static/', 1)[-1]

    fichier = Fichier(
        user_id=user_id,
        pub_id=pub_id,
        nom=nom_original,
        chemin=chemin_web,
        type_mime=mimetype,
        taille=taille,
    )
    db.session.add(fichier)
    return fichier


def type_publication_pour(fichier):
    if not fichier:
        return 'texte'
    return fichier.categorie  # 'photo' / 'video' / 'fichier'
