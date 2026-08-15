from flask_sqlalchemy import SQLAlchemy  # noqa: F401 (compat import order)
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ─────────────────────────────────────────────
#  1. UTILISATEURS
# ─────────────────────────────────────────────
class Utilisateur(db.Model):
    __tablename__ = 'utilisateurs'

    id         = db.Column(db.Integer, primary_key=True)
    nom        = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    photo      = db.Column(db.String(255), default='default.png')
    bio        = db.Column(db.Text)
    filiere    = db.Column(db.String(100))
    niveau     = db.Column(db.String(50))   # Licence 1, Master 2…
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    depenses       = db.relationship('Depense',       backref='utilisateur', lazy='dynamic')
    revenus        = db.relationship('Revenu',        backref='utilisateur', lazy='dynamic')
    taches         = db.relationship('Tache',         backref='utilisateur', lazy='dynamic')
    publications   = db.relationship('Publication',   backref='auteur',      lazy='dynamic')
    commentaires   = db.relationship('Commentaire',   backref='auteur',      lazy='dynamic')
    notifications  = db.relationship('Notification',  backref='utilisateur', lazy='dynamic')

    def set_password(self, password):
        self.mot_de_passe = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.mot_de_passe, password)

    def __repr__(self):
        return f'<Utilisateur {self.email}>'


# ─────────────────────────────────────────────
#  2. DÉPENSES
# ─────────────────────────────────────────────
CATEGORIES_DEPENSES = [
    'Alimentation', 'Transport', 'Logement', 'Santé',
    'Loisirs', 'Fournitures', 'Abonnements', 'Autre'
]

class Depense(db.Model):
    __tablename__ = 'depenses'

    id         = db.Column(db.Integer, primary_key=True)
    montant    = db.Column(db.Float, nullable=False)
    categorie  = db.Column(db.String(100), nullable=False)
    description= db.Column(db.String(255))
    date       = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    user_id    = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'montant': self.montant,
            'categorie': self.categorie, 'description': self.description,
            'date': self.date.isoformat()
        }


# ─────────────────────────────────────────────
#  3. REVENUS
# ─────────────────────────────────────────────
class Revenu(db.Model):
    __tablename__ = 'revenus'

    id       = db.Column(db.Integer, primary_key=True)
    montant  = db.Column(db.Float, nullable=False)
    source   = db.Column(db.String(100), nullable=False)  # Bourse, Job, Famille…
    date     = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    user_id  = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'montant': self.montant,
            'source': self.source, 'date': self.date.isoformat()
        }


# ─────────────────────────────────────────────
#  4. TÂCHES (Planificateur)
# ─────────────────────────────────────────────
class Tache(db.Model):
    __tablename__ = 'taches'

    id          = db.Column(db.Integer, primary_key=True)
    titre       = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    priorite    = db.Column(db.String(20), default='moyenne')  # haute / moyenne / basse
    statut      = db.Column(db.String(20), default='a_faire')  # a_faire / en_cours / termine
    date_limite = db.Column(db.DateTime)
    user_id     = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def score_urgence(self):
        """Calcule un score d'urgence 0-100 selon priorité + deadline."""
        if not self.date_limite:
            return 0
        delta = (self.date_limite - datetime.utcnow()).days
        prio_map = {'haute': 40, 'moyenne': 20, 'basse': 5}
        prio_score = prio_map.get(self.priorite, 10)
        time_score = max(0, 60 - delta * 2)
        return min(100, prio_score + time_score)

    def to_dict(self):
        return {
            'id': self.id, 'titre': self.titre,
            'priorite': self.priorite, 'statut': self.statut,
            'date_limite': self.date_limite.isoformat() if self.date_limite else None,
            'score_urgence': self.score_urgence
        }


# ─────────────────────────────────────────────
#  5. PUBLICATIONS (Feed UniShare)
# ─────────────────────────────────────────────
class Publication(db.Model):
    __tablename__ = 'publications'

    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    contenu  = db.Column(db.Text)
    type     = db.Column(db.String(20), default='texte')  # texte / photo / video / fichier / audio
    likes    = db.Column(db.Integer, default=0)
    date     = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    fichiers     = db.relationship('Fichier', foreign_keys='Fichier.pub_id', backref='publication', lazy='dynamic')
    audios       = db.relationship('Audio',       backref='publication', lazy='dynamic')
    commentaires = db.relationship('Commentaire', backref='publication', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id, 'contenu': self.contenu,
            'type': self.type, 'likes': self.likes,
            'date': self.date.isoformat(),
            'auteur': {'id': self.auteur.id, 'nom': self.auteur.nom, 'photo': self.auteur.photo}
        }


# ─────────────────────────────────────────────
#  6. FICHIERS
# ─────────────────────────────────────────────
class Fichier(db.Model):
    __tablename__ = 'fichiers'

    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    pub_id    = db.Column(db.Integer, db.ForeignKey('publications.id'), nullable=True)
    # Pièce jointe possible sur un message privé ou un message de groupe
    msg_prive_id  = db.Column(db.Integer, db.ForeignKey('messages_prives.id'), nullable=True)
    msg_groupe_id = db.Column(db.Integer, db.ForeignKey('messages_groupes.id'), nullable=True)
    nom       = db.Column(db.String(255), nullable=False)
    chemin    = db.Column(db.String(500), nullable=False)
    type_mime = db.Column(db.String(100))
    taille    = db.Column(db.Integer)   # en octets
    matiere   = db.Column(db.String(100))
    created_at= db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def categorie(self):
        """photo / video / audio / fichier — déduit du type MIME, pour l'affichage."""
        if not self.type_mime:
            return 'fichier'
        if self.type_mime.startswith('image/'):
            return 'photo'
        if self.type_mime.startswith('video/'):
            return 'video'
        if self.type_mime.startswith('audio/'):
            return 'audio'
        return 'fichier'


# ─────────────────────────────────────────────
#  7. AUDIOS (Messages vocaux)
# ─────────────────────────────────────────────
class Audio(db.Model):
    __tablename__ = 'audios'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    pub_id        = db.Column(db.Integer, db.ForeignKey('publications.id'), nullable=True)
    chemin        = db.Column(db.String(500), nullable=False)
    duree         = db.Column(db.Integer)         # secondes
    transcription = db.Column(db.Text)            # optionnel via IA
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
#  8. COMMENTAIRES
# ─────────────────────────────────────────────
class Commentaire(db.Model):
    __tablename__ = 'commentaires'

    id      = db.Column(db.Integer, primary_key=True)
    pub_id  = db.Column(db.Integer, db.ForeignKey('publications.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date    = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
#  9. NOTIFICATIONS
# ─────────────────────────────────────────────
class Notification(db.Model):
    __tablename__ = 'notifications'

    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    type    = db.Column(db.String(50))    # like / commentaire / message / rappel
    message = db.Column(db.String(255), nullable=False)
    lu      = db.Column(db.Boolean, default=False)
    lien    = db.Column(db.String(255))   # URL cible (optionnel)
    date    = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
#  10. MESSAGES PRIVÉS
# ─────────────────────────────────────────────
class MessagePrive(db.Model):
    __tablename__ = 'messages_prives'

    id              = db.Column(db.Integer, primary_key=True)
    expediteur_id   = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    destinataire_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    contenu         = db.Column(db.Text)
    type            = db.Column(db.String(20), default='texte')  # texte / photo / video / audio / fichier
    fichier_id      = db.Column(db.Integer, db.ForeignKey('fichiers.id'), nullable=True)
    lu              = db.Column(db.Boolean, default=False)
    modifie         = db.Column(db.Boolean, default=False)
    supprime        = db.Column(db.Boolean, default=False)
    date            = db.Column(db.DateTime, default=datetime.utcnow)

    expediteur   = db.relationship('Utilisateur', foreign_keys=[expediteur_id])
    destinataire = db.relationship('Utilisateur', foreign_keys=[destinataire_id])
    fichier      = db.relationship('Fichier', foreign_keys=[fichier_id])

    def to_dict(self):
        return {
            'id': self.id,
            'expediteur_id': self.expediteur_id,
            'destinataire_id': self.destinataire_id,
            'contenu': "Message supprimé" if self.supprime else self.contenu,
            'type': self.type,
            'modifie': self.modifie,
            'supprime': self.supprime,
            'date': self.date.strftime('%H:%M'),
            'fichier': None if self.supprime else (
                {'nom': self.fichier.nom, 'chemin': self.fichier.chemin, 'categorie': self.fichier.categorie} if self.fichier else None
            ),
        }


# ─────────────────────────────────────────────
#  11. GROUPES (discussions de groupe privées)
# ─────────────────────────────────────────────
class Groupe(db.Model):
    __tablename__ = 'groupes'

    id          = db.Column(db.Integer, primary_key=True)
    nom         = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(255))
    photo       = db.Column(db.String(255), default='default_groupe.png')
    createur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    membres  = db.relationship('GroupeMembre', backref='groupe', lazy='dynamic', cascade='all, delete-orphan')
    messages = db.relationship('MessageGroupe', backref='groupe', lazy='dynamic', cascade='all, delete-orphan')

    def est_membre(self, user_id):
        return self.membres.filter_by(user_id=user_id).first() is not None


class GroupeMembre(db.Model):
    __tablename__ = 'groupe_membres'

    id        = db.Column(db.Integer, primary_key=True)
    groupe_id = db.Column(db.Integer, db.ForeignKey('groupes.id'), nullable=False)
    user_id   = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    role      = db.Column(db.String(20), default='membre')  # admin / membre
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    utilisateur = db.relationship('Utilisateur')


class MessageGroupe(db.Model):
    __tablename__ = 'messages_groupes'

    id         = db.Column(db.Integer, primary_key=True)
    groupe_id  = db.Column(db.Integer, db.ForeignKey('groupes.id'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    contenu    = db.Column(db.Text)
    type       = db.Column(db.String(20), default='texte')  # texte / photo / video / audio / fichier
    fichier_id = db.Column(db.Integer, db.ForeignKey('fichiers.id'), nullable=True)
    modifie    = db.Column(db.Boolean, default=False)
    supprime   = db.Column(db.Boolean, default=False)
    date       = db.Column(db.DateTime, default=datetime.utcnow)

    auteur  = db.relationship('Utilisateur')
    fichier = db.relationship('Fichier', foreign_keys=[fichier_id])

    def to_dict(self):
        return {
            'id': self.id,
            'groupe_id': self.groupe_id,
            'user_id': self.user_id,
            'auteur_nom': self.auteur.nom,
            'contenu': "Message supprimé" if self.supprime else self.contenu,
            'type': self.type,
            'modifie': self.modifie,
            'supprime': self.supprime,
            'date': self.date.strftime('%H:%M'),
            'fichier': None if self.supprime else (
                {'nom': self.fichier.nom, 'chemin': self.fichier.chemin, 'categorie': self.fichier.categorie} if self.fichier else None
            ),
        }


# ─────────────────────────────────────────────
#  12. EFFACEMENT DE CONVERSATION (par utilisateur, comme WhatsApp)
#  Effacer une discussion ne supprime rien chez l'autre personne : on
#  retient juste, pour CET utilisateur, à partir de quand ne plus
#  afficher les anciens messages d'une conversation donnée.
# ─────────────────────────────────────────────
class EffacementConversation(db.Model):
    __tablename__ = 'effacements_conversation'

    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    autre_id  = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=True)   # conversation privée
    groupe_id = db.Column(db.Integer, db.ForeignKey('groupes.id'), nullable=True)        # conversation de groupe
    efface_le = db.Column(db.DateTime, default=datetime.utcnow)
