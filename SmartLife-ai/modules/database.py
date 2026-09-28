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
    role       = db.Column(db.String(30), nullable=False, default='etudiant', index=True)
    matricule  = db.Column(db.String(50), unique=True, nullable=True, index=True)
    statut     = db.Column(db.String(20), nullable=False, default='actif', index=True)
    activation_token_hash = db.Column(db.String(64), unique=True, nullable=True)
    activation_expires_at = db.Column(db.DateTime, nullable=True)
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
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


# ─────────────────────────────────────────────
#  13. ABONNEMENTS AUX NOTIFICATIONS PUSH
#  Un navigateur = un abonnement. Un utilisateur peut avoir plusieurs
#  abonnements (téléphone + PC par exemple) — on envoie à tous.
# ─────────────────────────────────────────────
class AbonnementPush(db.Model):
    __tablename__ = 'abonnements_push'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    endpoint   = db.Column(db.Text, nullable=False, unique=True)
    p256dh     = db.Column(db.String(255), nullable=False)
    auth       = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
#  20. STRUCTURE ACADÉMIQUE — ADMINISTRATION
# ─────────────────────────────────────────────
class AnneeAcademique(db.Model):
    __tablename__ = 'annees_academiques'
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(20), unique=True, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    niveaux = db.relationship('Niveau', backref='annee_academique', lazy=True)


class Filiere(db.Model):
    __tablename__ = 'filieres'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(150), unique=True, nullable=False)
    code = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    niveaux = db.relationship('Niveau', backref='filiere', lazy=True, cascade='all, delete-orphan')


class Niveau(db.Model):
    __tablename__ = 'niveaux'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False)
    code = db.Column(db.String(30), nullable=False)
    filiere_id = db.Column(db.Integer, db.ForeignKey('filieres.id', ondelete='CASCADE'), nullable=False)
    annee_academique_id = db.Column(db.Integer, db.ForeignKey('annees_academiques.id', ondelete='RESTRICT'), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    matieres = db.relationship('Matiere', backref='niveau', lazy=True, cascade='all, delete-orphan')


class Semestre(db.Model):
    __tablename__ = 'semestres'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False)
    code = db.Column(db.String(30), unique=True, nullable=False)
    ordre = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    matieres = db.relationship('Matiere', backref='semestre', lazy=True)


class Professeur(db.Model):
    __tablename__ = 'professeurs'
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id', ondelete='SET NULL'), unique=True, nullable=True)
    nom = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    telephone = db.Column(db.String(40))
    matricule = db.Column(db.String(50), unique=True)
    specialite = db.Column(db.String(150))
    actif = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    utilisateur = db.relationship('Utilisateur', backref=db.backref('profil_professeur', uselist=False))
    matieres = db.relationship('Matiere', backref='professeur', lazy=True)


class Matiere(db.Model):
    __tablename__ = 'matieres'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), nullable=False)
    nom = db.Column(db.String(150), nullable=False)
    coefficient = db.Column(db.Numeric(5, 2), nullable=False, default=1)
    credits = db.Column(db.Numeric(5, 2), nullable=False, default=1)
    seuil_validation = db.Column(db.Numeric(5, 2), nullable=False, default=10)
    niveau_id = db.Column(db.Integer, db.ForeignKey('niveaux.id', ondelete='CASCADE'), nullable=False)
    semestre_id = db.Column(db.Integer, db.ForeignKey('semestres.id', ondelete='RESTRICT'), nullable=False)
    professeur_id = db.Column(db.Integer, db.ForeignKey('professeurs.id', ondelete='SET NULL'), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('code', 'niveau_id', name='uq_matiere_code_niveau'),
    )

# ─────────────────────────────────────────────
#  21. PRÉINSCRIPTIONS ET INSCRIPTIONS ÉTUDIANTS
# ─────────────────────────────────────────────
class Preinscription(db.Model):
    __tablename__ = 'preinscriptions'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, index=True)
    telephone = db.Column(db.String(40), nullable=False)
    date_naissance = db.Column(db.Date)
    lieu_naissance = db.Column(db.String(150))
    adresse = db.Column(db.String(255))
    filiere_id = db.Column(db.Integer, db.ForeignKey('filieres.id', ondelete='RESTRICT'), nullable=False)
    niveau_id = db.Column(db.Integer, db.ForeignKey('niveaux.id', ondelete='RESTRICT'), nullable=False)
    annee_academique_id = db.Column(db.Integer, db.ForeignKey('annees_academiques.id', ondelete='RESTRICT'), nullable=False)
    statut = db.Column(db.String(20), nullable=False, default='en_attente', index=True)
    motif_admin = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    filiere = db.relationship('Filiere', backref=db.backref('preinscriptions', lazy=True))
    niveau = db.relationship('Niveau', backref=db.backref('preinscriptions', lazy=True))
    annee_academique = db.relationship('AnneeAcademique', backref=db.backref('preinscriptions', lazy=True))


class InscriptionEtudiant(db.Model):
    __tablename__ = 'inscriptions_etudiants'

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id', ondelete='CASCADE'), nullable=False)
    matricule = db.Column(db.String(50), unique=True, nullable=False)
    filiere_id = db.Column(db.Integer, db.ForeignKey('filieres.id', ondelete='RESTRICT'), nullable=False)
    niveau_id = db.Column(db.Integer, db.ForeignKey('niveaux.id', ondelete='RESTRICT'), nullable=False)
    annee_academique_id = db.Column(db.Integer, db.ForeignKey('annees_academiques.id', ondelete='RESTRICT'), nullable=False)
    statut = db.Column(db.String(20), nullable=False, default='actif', index=True)
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('utilisateur_id', 'annee_academique_id', name='uq_inscription_etudiant_annee'),
    )

    utilisateur = db.relationship('Utilisateur', backref=db.backref('inscriptions_academiques', lazy=True))
    filiere = db.relationship('Filiere', backref=db.backref('inscriptions_etudiants', lazy=True))
    niveau = db.relationship('Niveau', backref=db.backref('inscriptions_etudiants', lazy=True))
    annee_academique = db.relationship('AnneeAcademique', backref=db.backref('inscriptions_etudiants', lazy=True))

# ─────────────────────────────────────────────
#  22. ÉVALUATIONS, NOTES ET RÉSULTATS
# ─────────────────────────────────────────────
class EvaluationType(db.Model):
    __tablename__ = 'evaluation_types'
    id = db.Column(db.Integer, primary_key=True)
    matiere_id = db.Column(db.Integer, db.ForeignKey('matieres.id', ondelete='CASCADE'), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    poids = db.Column(db.Numeric(6, 2), nullable=False, default=1)
    note_sur = db.Column(db.Numeric(6, 2), nullable=False, default=20)
    ordre = db.Column(db.Integer, nullable=False, default=1)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    matiere = db.relationship('Matiere', backref=db.backref('evaluations_types', lazy=True, cascade='all, delete-orphan'))


class NoteEvaluation(db.Model):
    __tablename__ = 'notes_evaluations'
    id = db.Column(db.Integer, primary_key=True)
    inscription_id = db.Column(db.Integer, db.ForeignKey('inscriptions_etudiants.id', ondelete='CASCADE'), nullable=False)
    evaluation_type_id = db.Column(db.Integer, db.ForeignKey('evaluation_types.id', ondelete='CASCADE'), nullable=False)
    note = db.Column(db.Numeric(6, 2), nullable=False)
    commentaire = db.Column(db.Text)
    saisi_par_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('inscription_id', 'evaluation_type_id', name='uq_note_etudiant_evaluation'),)
    inscription = db.relationship('InscriptionEtudiant', backref=db.backref('notes_evaluations', lazy=True, cascade='all, delete-orphan'))
    evaluation_type = db.relationship('EvaluationType', backref=db.backref('notes', lazy=True, cascade='all, delete-orphan'))


class ResultatMatiere(db.Model):
    __tablename__ = 'resultats_matieres'
    id = db.Column(db.Integer, primary_key=True)
    inscription_id = db.Column(db.Integer, db.ForeignKey('inscriptions_etudiants.id', ondelete='CASCADE'), nullable=False)
    matiere_id = db.Column(db.Integer, db.ForeignKey('matieres.id', ondelete='CASCADE'), nullable=False)
    semestre_id = db.Column(db.Integer, db.ForeignKey('semestres.id', ondelete='RESTRICT'), nullable=False)
    note_finale = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    moyenne_sur = db.Column(db.Numeric(6, 2), nullable=False, default=20)
    valide = db.Column(db.Boolean, nullable=False, default=False)
    publie = db.Column(db.Boolean, nullable=False, default=False, index=True)
    publie_le = db.Column(db.DateTime)
    commentaire = db.Column(db.Text)
    statut = db.Column(db.String(20), nullable=False, default='brouillon', index=True)
    soumis_le = db.Column(db.DateTime)
    valide_le = db.Column(db.DateTime)
    valide_par_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id', ondelete='SET NULL'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    valide_par = db.relationship('Utilisateur', foreign_keys=[valide_par_id])
    __table_args__ = (db.UniqueConstraint('inscription_id', 'matiere_id', name='uq_resultat_etudiant_matiere'),)
    inscription = db.relationship('InscriptionEtudiant', backref=db.backref('resultats_matieres', lazy=True, cascade='all, delete-orphan'))
    matiere = db.relationship('Matiere', backref=db.backref('resultats', lazy=True))
    semestre = db.relationship('Semestre')

# ─────────────────────────────────────────────
#  23. SYNTHÈSES SEMESTRIELLES ET RÈGLES ACADÉMIQUES
# ─────────────────────────────────────────────
class ReglePassage(db.Model):
    __tablename__ = 'regles_passage'
    id = db.Column(db.Integer, primary_key=True)
    annee_academique_id = db.Column(db.Integer, db.ForeignKey('annees_academiques.id', ondelete='CASCADE'), nullable=False, unique=True)
    moyenne_min = db.Column(db.Numeric(5, 2), nullable=False, default=10)
    credits_min = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    compensation_autorisee = db.Column(db.Boolean, nullable=False, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    annee_academique = db.relationship('AnneeAcademique', backref=db.backref('regle_passage', uselist=False))


class BulletinSemestre(db.Model):
    __tablename__ = 'bulletins_semestres'
    id = db.Column(db.Integer, primary_key=True)
    inscription_id = db.Column(db.Integer, db.ForeignKey('inscriptions_etudiants.id', ondelete='CASCADE'), nullable=False)
    semestre_id = db.Column(db.Integer, db.ForeignKey('semestres.id', ondelete='RESTRICT'), nullable=False)
    moyenne = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    total_credits = db.Column(db.Numeric(7, 2), nullable=False, default=0)
    credits_valides = db.Column(db.Numeric(7, 2), nullable=False, default=0)
    matieres_validees = db.Column(db.Integer, nullable=False, default=0)
    matieres_total = db.Column(db.Integer, nullable=False, default=0)
    publie = db.Column(db.Boolean, nullable=False, default=False, index=True)
    decision = db.Column(db.String(40), nullable=False, default='En cours')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('inscription_id', 'semestre_id', name='uq_bulletin_inscription_semestre'),)
    inscription = db.relationship('InscriptionEtudiant', backref=db.backref('bulletins_semestres', lazy=True, cascade='all, delete-orphan'))
    semestre = db.relationship('Semestre', backref=db.backref('bulletins', lazy=True))
