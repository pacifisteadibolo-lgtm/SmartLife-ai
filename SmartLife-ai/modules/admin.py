from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from datetime import datetime, timedelta
import hashlib
import re
import secrets
from modules.database import (
    db, Utilisateur, AnneeAcademique, Filiere, Niveau,
    Semestre, Professeur, Matiere, Preinscription, InscriptionEtudiant, EvaluationType, NoteEvaluation, ResultatMatiere
)
from utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')


def _commit_or_error(message='Opération impossible. Vérifie les données.'):
    try:
        db.session.commit()
        flash(message, 'success')
        return True
    except IntegrityError:
        db.session.rollback()
        flash('Cette donnée existe déjà ou est encore utilisée ailleurs.', 'error')
        return False


@admin_bp.route('/')
@admin_required
def accueil():
    return render_template(
        'admin/dashboard.html',
        total_etudiants=Utilisateur.query.filter_by(role='etudiant').count(),
        etudiants_actifs=Utilisateur.query.filter_by(role='etudiant', statut='actif').count(),
        etudiants_inactifs=Utilisateur.query.filter_by(role='etudiant', statut='inactif').count(),
        total_admins=Utilisateur.query.filter_by(role='administrateur').count(),
        total_filieres=Filiere.query.count(),
        total_matieres=Matiere.query.count(),
        total_professeurs=Professeur.query.filter_by(actif=True).count(),
        preinscriptions_en_attente=Preinscription.query.filter_by(statut='en_attente').count(),
        comptes_professeurs=Utilisateur.query.filter_by(role='professeur').count(),
    )


@admin_bp.route('/annees', methods=['GET', 'POST'])
@admin_required
def annees():
    if request.method == 'POST':
        libelle = request.form.get('libelle', '').strip()
        if not libelle:
            flash('Le libellé de l’année est obligatoire.', 'error')
        else:
            if request.form.get('active'):
                AnneeAcademique.query.update({AnneeAcademique.active: False})
            db.session.add(AnneeAcademique(libelle=libelle, active=bool(request.form.get('active'))))
            if _commit_or_error('Année académique ajoutée.'):
                return redirect(url_for('admin.annees'))
    return render_template('admin/annees.html', annees=AnneeAcademique.query.order_by(AnneeAcademique.libelle.desc()).all())


@admin_bp.route('/annees/<int:annee_id>/activer', methods=['POST'])
@admin_required
def activer_annee(annee_id):
    annee = db.session.get(AnneeAcademique, annee_id)
    if not annee:
        flash('Année académique introuvable.', 'error')
    else:
        AnneeAcademique.query.update({AnneeAcademique.active: False})
        annee.active = True
        _commit_or_error('Année académique activée.')
    return redirect(url_for('admin.annees'))


@admin_bp.route('/filieres', methods=['GET', 'POST'])
@admin_required
def filieres():
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        code = request.form.get('code', '').strip().upper()
        description = request.form.get('description', '').strip() or None
        if not nom or not code:
            flash('Le nom et le code de la filière sont obligatoires.', 'error')
        else:
            db.session.add(Filiere(nom=nom, code=code, description=description))
            if _commit_or_error('Filière ajoutée.'):
                return redirect(url_for('admin.filieres'))
    return render_template('admin/filieres.html', filieres=Filiere.query.order_by(Filiere.nom).all())


@admin_bp.route('/niveaux', methods=['GET', 'POST'])
@admin_required
def niveaux():
    filieres = Filiere.query.filter_by(active=True).order_by(Filiere.nom).all()
    annees = AnneeAcademique.query.order_by(AnneeAcademique.libelle.desc()).all()
    if request.method == 'POST':
        try:
            niveau = Niveau(
                nom=request.form.get('nom', '').strip(),
                code=request.form.get('code', '').strip().upper(),
                filiere_id=int(request.form['filiere_id']),
                annee_academique_id=int(request.form['annee_academique_id']),
            )
            if not niveau.nom or not niveau.code:
                raise ValueError
            db.session.add(niveau)
            if _commit_or_error('Niveau ajouté.'):
                return redirect(url_for('admin.niveaux'))
        except (ValueError, KeyError):
            db.session.rollback()
            flash('Les informations du niveau sont invalides.', 'error')
    niveaux = Niveau.query.join(Filiere).join(AnneeAcademique).order_by(Filiere.nom, Niveau.nom).all()
    return render_template('admin/niveaux.html', niveaux=niveaux, filieres=filieres, annees=annees)


@admin_bp.route('/semestres', methods=['GET', 'POST'])
@admin_required
def semestres():
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        code = request.form.get('code', '').strip().upper()
        try:
            ordre = int(request.form.get('ordre', '1'))
        except ValueError:
            ordre = 1
        if not nom or not code:
            flash('Le nom et le code du semestre sont obligatoires.', 'error')
        else:
            db.session.add(Semestre(nom=nom, code=code, ordre=ordre))
            if _commit_or_error('Semestre ajouté.'):
                return redirect(url_for('admin.semestres'))
    return render_template('admin/semestres.html', semestres=Semestre.query.order_by(Semestre.ordre).all())


@admin_bp.route('/professeurs', methods=['GET', 'POST'])
@admin_required
def professeurs():
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        if not nom:
            flash('Le nom du professeur est obligatoire.', 'error')
        else:
            db.session.add(Professeur(
                nom=nom,
                email=request.form.get('email', '').strip() or None,
                telephone=request.form.get('telephone', '').strip() or None,
                matricule=request.form.get('matricule', '').strip() or None,
                specialite=request.form.get('specialite', '').strip() or None,
            ))
            if _commit_or_error('Professeur ajouté.'):
                return redirect(url_for('admin.professeurs'))
    return render_template('admin/professeurs.html', professeurs=Professeur.query.order_by(Professeur.nom).all())


@admin_bp.route('/professeurs/<int:professeur_id>/creer-compte', methods=['POST'])
@admin_required
def creer_compte_professeur(professeur_id):
    professeur = db.session.get(Professeur, professeur_id)
    if not professeur:
        flash('Professeur introuvable.', 'error')
        return redirect(url_for('admin.professeurs'))
    if professeur.utilisateur_id:
        flash('Ce professeur possède déjà un compte.', 'error')
        return redirect(url_for('admin.professeurs'))
    email = (professeur.email or '').strip().lower()
    if not email:
        flash('Un email est obligatoire pour créer le compte professeur.', 'error')
        return redirect(url_for('admin.professeurs'))
    if Utilisateur.query.filter_by(email=email).first():
        flash('Cet email est déjà utilisé par un compte.', 'error')
        return redirect(url_for('admin.professeurs'))

    token = secrets.token_urlsafe(32)
    utilisateur = Utilisateur(
        nom=professeur.nom, email=email, role='professeur', statut='actif',
        activation_token_hash=hashlib.sha256(token.encode()).hexdigest(),
        activation_expires_at=datetime.utcnow() + timedelta(hours=48),
        must_change_password=True
    )
    utilisateur.set_password(secrets.token_urlsafe(32))
    db.session.add(utilisateur)
    db.session.flush()
    professeur.utilisateur_id = utilisateur.id
    db.session.commit()
    activation_url = url_for('auth.activation', token=token, _external=True)
    return render_template('admin/compte_professeur_cree.html', professeur=professeur, utilisateur=utilisateur, activation_url=activation_url)


@admin_bp.route('/professeurs/<int:professeur_id>/statut', methods=['POST'])
@admin_required
def changer_statut_professeur(professeur_id):
    professeur = db.session.get(Professeur, professeur_id)
    if not professeur:
        flash('Professeur introuvable.', 'error')
        return redirect(url_for('admin.professeurs'))
    professeur.actif = request.form.get('actif') == '1'
    if professeur.utilisateur:
        professeur.utilisateur.statut = 'actif' if professeur.actif else 'inactif'
    if _commit_or_error('Statut du professeur mis à jour.'):
        return redirect(url_for('admin.professeurs'))
    return redirect(url_for('admin.professeurs'))


@admin_bp.route('/comptes')
@admin_required
def comptes():
    role = request.args.get('role', 'tous')
    statuts = {'actif','inactif'}
    query = Utilisateur.query
    if role in {'etudiant','professeur','administrateur'}:
        query = query.filter_by(role=role)
    if request.args.get('statut') in statuts:
        query = query.filter_by(statut=request.args['statut'])
    comptes = query.order_by(Utilisateur.role, Utilisateur.nom).all()
    return render_template('admin/comptes.html', comptes=comptes, role=role)


@admin_bp.route('/comptes/<int:utilisateur_id>/statut', methods=['POST'])
@admin_required
def changer_statut_compte(utilisateur_id):
    utilisateur = db.session.get(Utilisateur, utilisateur_id)
    if not utilisateur:
        flash('Compte introuvable.', 'error')
        return redirect(url_for('admin.comptes'))
    if utilisateur.id == session.get('user_id'):
        flash('Tu ne peux pas désactiver ton propre compte administrateur.', 'error')
        return redirect(url_for('admin.comptes'))
    utilisateur.statut = 'actif' if request.form.get('statut') == 'actif' else 'inactif'
    if utilisateur.profil_professeur and utilisateur.statut == 'inactif':
        utilisateur.profil_professeur.actif = False
    if _commit_or_error('Statut du compte mis à jour.'):
        return redirect(url_for('admin.comptes'))
    return redirect(url_for('admin.comptes'))


@admin_bp.route('/matieres', methods=['GET', 'POST'])
@admin_required
def matieres():
    niveaux = Niveau.query.filter_by(active=True).order_by(Niveau.nom).all()
    semestres = Semestre.query.order_by(Semestre.ordre).all()
    professeurs = Professeur.query.filter_by(actif=True).order_by(Professeur.nom).all()
    if request.method == 'POST':
        try:
            matiere = Matiere(
                code=request.form.get('code', '').strip().upper(),
                nom=request.form.get('nom', '').strip(),
                coefficient=float(request.form.get('coefficient', '1')),
                credits=float(request.form.get('credits', '1')),
                niveau_id=int(request.form['niveau_id']),
                semestre_id=int(request.form['semestre_id']),
                professeur_id=int(request.form['professeur_id']) if request.form.get('professeur_id') else None,
            )
            if not matiere.code or not matiere.nom or matiere.coefficient <= 0 or matiere.credits < 0:
                raise ValueError
            db.session.add(matiere)
            if _commit_or_error('Matière ajoutée.'):
                return redirect(url_for('admin.matieres'))
        except (ValueError, KeyError):
            db.session.rollback()
            flash('Les informations de la matière sont invalides.', 'error')
    liste = Matiere.query.join(Niveau).join(Filiere).join(Semestre).order_by(Filiere.nom, Niveau.nom, Semestre.ordre, Matiere.nom).all()
    return render_template('admin/matieres.html', matieres=liste, niveaux=niveaux, semestres=semestres, professeurs=professeurs)


@admin_bp.route('/preinscriptions')
@admin_required
def preinscriptions():
    statut = request.args.get('statut', 'en_attente')
    statuts_valides = {'en_attente', 'acceptee', 'refusee', 'incomplete', 'toutes'}
    if statut not in statuts_valides:
        statut = 'en_attente'
    query = Preinscription.query.order_by(Preinscription.created_at.desc())
    if statut != 'toutes':
        query = query.filter_by(statut=statut)
    return render_template('admin/preinscriptions.html', preinscriptions=query.all(), statut=statut)


@admin_bp.route('/preinscriptions/<int:preinscription_id>')
@admin_required
def preinscription_detail(preinscription_id):
    dossier = db.session.get(Preinscription, preinscription_id)
    if not dossier:
        flash('Préinscription introuvable.', 'error')
        return redirect(url_for('admin.preinscriptions'))
    return render_template('admin/preinscription_detail.html', dossier=dossier)


def _generer_matricule(annee):
    """Génère un matricule lisible et unique : ETU-AAAA-0001."""
    match = re.search(r'(20\d{2})', annee.libelle or '')
    annee_code = match.group(1) if match else str(datetime.utcnow().year)
    prefix = f'ETU-{annee_code}-'
    derniers = InscriptionEtudiant.query.filter(InscriptionEtudiant.matricule.like(prefix + '%')).all()
    max_num = 0
    for inscription in derniers:
        suffix = inscription.matricule[len(prefix):]
        if suffix.isdigit():
            max_num = max(max_num, int(suffix))
    return f'{prefix}{max_num + 1:04d}'


@admin_bp.route('/preinscriptions/<int:preinscription_id>/accepter', methods=['POST'])
@admin_required
def accepter_preinscription(preinscription_id):
    dossier = db.session.get(Preinscription, preinscription_id)
    if not dossier:
        flash('Préinscription introuvable.', 'error')
        return redirect(url_for('admin.preinscriptions'))
    if dossier.statut == 'acceptee':
        flash('Cette préinscription est déjà acceptée.', 'error')
        return redirect(url_for('admin.preinscription_detail', preinscription_id=dossier.id))

    if Utilisateur.query.filter_by(email=dossier.email).first():
        flash('Un compte existe déjà avec cet email. Vérifie le dossier avant de l’accepter.', 'error')
        return redirect(url_for('admin.preinscription_detail', preinscription_id=dossier.id))

    matricule = _generer_matricule(dossier.annee_academique)
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    nom_complet = f'{dossier.prenom} {dossier.nom}'.strip()
    utilisateur = Utilisateur(
        nom=nom_complet,
        email=dossier.email,
        role='etudiant',
        matricule=matricule,
        statut='actif',
        activation_token_hash=token_hash,
        activation_expires_at=datetime.utcnow() + timedelta(hours=48),
        filiere=dossier.filiere.nom,
        niveau=dossier.niveau.nom,
    )
    utilisateur.set_password(secrets.token_urlsafe(32))
    db.session.add(utilisateur)
    db.session.flush()

    inscription = InscriptionEtudiant(
        utilisateur_id=utilisateur.id,
        matricule=matricule,
        filiere_id=dossier.filiere_id,
        niveau_id=dossier.niveau_id,
        annee_academique_id=dossier.annee_academique_id,
        statut='actif',
    )
    db.session.add(inscription)
    dossier.statut = 'acceptee'
    dossier.motif_admin = request.form.get('motif_admin', '').strip() or None
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Impossible de créer l’étudiant. Vérifie l’email et le matricule.', 'error')
        return redirect(url_for('admin.preinscription_detail', preinscription_id=dossier.id))

    activation_url = url_for('auth.activation', token=token, _external=True)
    return render_template('admin/acceptation_reussie.html', dossier=dossier, utilisateur=utilisateur, activation_url=activation_url)


@admin_bp.route('/preinscriptions/<int:preinscription_id>/refuser', methods=['POST'])
@admin_required
def refuser_preinscription(preinscription_id):
    dossier = db.session.get(Preinscription, preinscription_id)
    if not dossier:
        flash('Préinscription introuvable.', 'error')
        return redirect(url_for('admin.preinscriptions'))
    dossier.statut = 'refusee'
    dossier.motif_admin = request.form.get('motif_admin', '').strip() or 'Dossier refusé par l’administration.'
    if _commit_or_error('Préinscription refusée.'):
        return redirect(url_for('admin.preinscriptions'))
    return redirect(url_for('admin.preinscription_detail', preinscription_id=dossier.id))


@admin_bp.route('/etudiants')
@admin_required
def etudiants():
    recherche = request.args.get('q', '').strip()
    statut = request.args.get('statut', 'actif')
    query = InscriptionEtudiant.query.join(Utilisateur).join(Filiere).join(Niveau).join(AnneeAcademique)
    if recherche:
        terme = f'%{recherche}%'
        query = query.filter(or_(Utilisateur.nom.ilike(terme), Utilisateur.email.ilike(terme), InscriptionEtudiant.matricule.ilike(terme)))
    if statut in {'actif', 'inactif'}:
        query = query.filter(InscriptionEtudiant.statut == statut)
    liste = query.order_by(Utilisateur.nom).all()
    return render_template('admin/etudiants.html', etudiants=liste, recherche=recherche, statut=statut)


@admin_bp.route('/etudiants/<int:inscription_id>')
@admin_required
def etudiant_detail(inscription_id):
    inscription = db.session.get(InscriptionEtudiant, inscription_id)
    if not inscription:
        flash('Étudiant introuvable.', 'error')
        return redirect(url_for('admin.etudiants'))
    return render_template('admin/etudiant_detail.html', inscription=inscription)


@admin_bp.route('/etudiants/<int:inscription_id>/statut', methods=['POST'])
@admin_required
def modifier_statut_etudiant(inscription_id):
    inscription = db.session.get(InscriptionEtudiant, inscription_id)
    if not inscription:
        flash('Étudiant introuvable.', 'error')
        return redirect(url_for('admin.etudiants'))
    nouveau = request.form.get('statut')
    if nouveau not in {'actif', 'inactif'}:
        flash('Statut invalide.', 'error')
        return redirect(url_for('admin.etudiant_detail', inscription_id=inscription.id))
    inscription.statut = nouveau
    inscription.utilisateur.statut = nouveau
    if _commit_or_error('Statut de l’étudiant mis à jour.'):
        return redirect(url_for('admin.etudiant_detail', inscription_id=inscription.id))
    return redirect(url_for('admin.etudiant_detail', inscription_id=inscription.id))

# ─────────────────────────────────────────────
# NOTES & RÉSULTATS
# ─────────────────────────────────────────────
def _calculer_note_finale(matiere, inscription):
    types = (EvaluationType.query
             .filter_by(matiere_id=matiere.id, active=True)
             .order_by(EvaluationType.ordre, EvaluationType.id).all())
    if not types:
        return None
    total_poids = sum(float(t.poids) for t in types)
    if total_poids <= 0:
        return None
    notes = {n.evaluation_type_id: n for n in NoteEvaluation.query.filter_by(inscription_id=inscription.id).all()}
    total = 0.0
    for t in types:
        n = notes.get(t.id)
        if n is None:
            return None
        valeur = float(n.note)
        sur = float(t.note_sur)
        if sur <= 0 or valeur < 0 or valeur > sur:
            return None
        total += (valeur / sur) * 20.0 * float(t.poids)
    return round(total / total_poids, 2)


@admin_bp.route('/notes')
@admin_required
def notes_index():
    matieres = (Matiere.query.join(Niveau).join(Filiere).join(Semestre)
                .filter(Matiere.active.is_(True))
                .order_by(Filiere.nom, Niveau.nom, Semestre.ordre, Matiere.nom).all())
    return render_template('admin/notes_index.html', matieres=matieres)


@admin_bp.route('/notes/matiere/<int:matiere_id>', methods=['GET', 'POST'])
@admin_required
def notes_matiere(matiere_id):
    matiere = db.session.get(Matiere, matiere_id)
    if not matiere:
        flash('Matière introuvable.', 'error')
        return redirect(url_for('admin.notes_index'))

    if request.method == 'POST':
        action = request.form.get('action')
        try:
            if action == 'ajouter_evaluation':
                nom = request.form.get('nom', '').strip()
                poids = float(request.form.get('poids', '1'))
                note_sur = float(request.form.get('note_sur', '20'))
                ordre = int(request.form.get('ordre', '1'))
                if not nom or poids <= 0 or note_sur <= 0:
                    raise ValueError
                db.session.add(EvaluationType(matiere_id=matiere.id, nom=nom, poids=poids, note_sur=note_sur, ordre=ordre))
                if _commit_or_error('Méthode d’évaluation ajoutée.'):
                    return redirect(url_for('admin.notes_matiere', matiere_id=matiere.id))
            elif action == 'enregistrer_notes':
                types = EvaluationType.query.filter_by(matiere_id=matiere.id, active=True).order_by(EvaluationType.ordre, EvaluationType.id).all()
                inscriptions = (InscriptionEtudiant.query.filter_by(niveau_id=matiere.niveau_id, statut='actif').all())
                for inscription in inscriptions:
                    for t in types:
                        raw = request.form.get(f'note_{inscription.id}_{t.id}', '').strip()
                        if raw == '':
                            continue
                        valeur = float(raw)
                        if valeur < 0 or valeur > float(t.note_sur):
                            raise ValueError(f'Note invalide pour {inscription.utilisateur.nom}.')
                        note = NoteEvaluation.query.filter_by(inscription_id=inscription.id, evaluation_type_id=t.id).first()
                        if note is None:
                            note = NoteEvaluation(inscription_id=inscription.id, evaluation_type_id=t.id)
                            db.session.add(note)
                        note.note = valeur
                        note.saisi_par_id = session.get('user_id')
                    final = _calculer_note_finale(matiere, inscription)
                    if final is not None:
                        resultat = ResultatMatiere.query.filter_by(inscription_id=inscription.id, matiere_id=matiere.id).first()
                        if resultat is None:
                            resultat = ResultatMatiere(inscription_id=inscription.id, matiere_id=matiere.id, semestre_id=matiere.semestre_id)
                            db.session.add(resultat)
                        resultat.note_finale = final
                        resultat.moyenne_sur = 20
                        resultat.valide = final >= float(matiere.seuil_validation)
                if _commit_or_error('Notes enregistrées et résultats recalculés.'):
                    return redirect(url_for('admin.notes_matiere', matiere_id=matiere.id))
            elif action == 'publier':
                inscriptions = InscriptionEtudiant.query.filter_by(niveau_id=matiere.niveau_id, statut='actif').all()
                now = datetime.utcnow()
                count = 0
                for inscription in inscriptions:
                    final = _calculer_note_finale(matiere, inscription)
                    if final is None:
                        continue
                    resultat = ResultatMatiere.query.filter_by(inscription_id=inscription.id, matiere_id=matiere.id).first()
                    if resultat is None:
                        resultat = ResultatMatiere(inscription_id=inscription.id, matiere_id=matiere.id, semestre_id=matiere.semestre_id)
                        db.session.add(resultat)
                    resultat.note_finale = final
                    resultat.valide = final >= float(matiere.seuil_validation)
                    if resultat.statut != 'valide':
                        continue
                    resultat.publie = True
                    resultat.statut = 'publie'
                    resultat.publie_le = now
                    count += 1
                db.session.commit()
                flash(f'{count} résultat(s) publié(s).', 'success')
                return redirect(url_for('admin.notes_matiere', matiere_id=matiere.id))
        except (ValueError, KeyError):
            db.session.rollback()
            flash('Une note ou une méthode d’évaluation est invalide.', 'error')

    types = EvaluationType.query.filter_by(matiere_id=matiere.id, active=True).order_by(EvaluationType.ordre, EvaluationType.id).all()
    inscriptions = (InscriptionEtudiant.query.filter_by(niveau_id=matiere.niveau_id, statut='actif')
                    .join(Utilisateur).order_by(Utilisateur.nom).all())
    notes = NoteEvaluation.query.filter(NoteEvaluation.inscription_id.in_([i.id for i in inscriptions])).all() if inscriptions else []
    notes_map = {(n.inscription_id, n.evaluation_type_id): n for n in notes}
    resultats = ResultatMatiere.query.filter(ResultatMatiere.matiere_id == matiere.id,
                                              ResultatMatiere.inscription_id.in_([i.id for i in inscriptions])).all() if inscriptions else []
    resultats_map = {r.inscription_id: r for r in resultats}
    return render_template('admin/notes_matiere.html', matiere=matiere, types=types,
                           inscriptions=inscriptions, notes_map=notes_map, resultats_map=resultats_map)


@admin_bp.route('/notes/resultat/<int:resultat_id>/valider', methods=['POST'])
@admin_required
def valider_resultat(resultat_id):
    resultat = db.session.get(ResultatMatiere, resultat_id)
    if not resultat:
        flash('Résultat introuvable.', 'error')
        return redirect(url_for('admin.notes_index'))
    if resultat.statut != 'soumis':
        flash('Seuls les résultats soumis par un professeur peuvent être validés.', 'error')
        return redirect(url_for('admin.notes_matiere', matiere_id=resultat.matiere_id))
    resultat.statut = 'valide'
    resultat.valide_le = datetime.utcnow()
    resultat.valide_par_id = session.get('user_id')
    db.session.commit()
    flash('Résultat validé. Il peut maintenant être publié.', 'success')
    return redirect(url_for('admin.notes_matiere', matiere_id=resultat.matiere_id))


@admin_bp.route('/notes/evaluation/<int:evaluation_id>/supprimer', methods=['POST'])
@admin_required
def supprimer_evaluation(evaluation_id):
    evaluation = db.session.get(EvaluationType, evaluation_id)
    if not evaluation:
        flash('Évaluation introuvable.', 'error')
        return redirect(url_for('admin.notes_index'))
    matiere_id = evaluation.matiere_id
    evaluation.active = False
    if _commit_or_error('Évaluation désactivée.'):
        return redirect(url_for('admin.notes_matiere', matiere_id=matiere_id))
    return redirect(url_for('admin.notes_matiere', matiere_id=matiere_id))


# ─────────────────────────────────────────────
# BULLETINS & RÈGLES DE PASSAGE
# ─────────────────────────────────────────────
def _calculer_bulletin(inscription, semestre):
    resultats = (ResultatMatiere.query
                 .filter_by(inscription_id=inscription.id, semestre_id=semestre.id, publie=True)
                 .join(ResultatMatiere.matiere).all())
    if not resultats:
        return None
    total_coeff = sum(float(r.matiere.coefficient) for r in resultats)
    total_credits = sum(float(r.matiere.credits) for r in resultats)
    credits_valides = sum(float(r.matiere.credits) for r in resultats if r.valide)
    moyenne = (sum(float(r.note_finale) * float(r.matiere.coefficient) for r in resultats) / total_coeff) if total_coeff else 0
    regle = ReglePassage.query.filter_by(annee_academique_id=inscription.annee_academique_id).first()
    moyenne_min = float(regle.moyenne_min) if regle else 10
    credits_min = float(regle.credits_min) if regle else total_credits
    if moyenne >= moyenne_min and credits_valides >= credits_min:
        decision = 'Validé'
    elif regle and regle.compensation_autorisee and moyenne >= moyenne_min and credits_valides > 0:
        decision = 'Validé par compensation'
    else:
        decision = 'À rattraper'
    return dict(moyenne=round(moyenne, 2), total_credits=round(total_credits, 2), credits_valides=round(credits_valides, 2),
                matieres_validees=sum(1 for r in resultats if r.valide), matieres_total=len(resultats), decision=decision)


@admin_bp.route('/bulletins')
@admin_required
def bulletins():
    annees = AnneeAcademique.query.order_by(AnneeAcademique.libelle.desc()).all()
    semestres = Semestre.query.order_by(Semestre.ordre).all()
    annee_id = request.args.get('annee_id', type=int)
    semestre_id = request.args.get('semestre_id', type=int)
    inscriptions = InscriptionEtudiant.query.filter_by(statut='actif')
    if annee_id:
        inscriptions = inscriptions.filter_by(annee_academique_id=annee_id)
    inscriptions = inscriptions.join(Utilisateur).order_by(Utilisateur.nom).all()
    lignes = []
    for inscription in inscriptions:
        for semestre in semestres:
            if semestre_id and semestre.id != semestre_id:
                continue
            data = _calculer_bulletin(inscription, semestre)
            if data:
                bulletin = BulletinSemestre.query.filter_by(inscription_id=inscription.id, semestre_id=semestre.id).first()
                lignes.append((inscription, semestre, data, bulletin))
    return render_template('admin/bulletins.html', annees=annees, semestres=semestres, lignes=lignes,
                           annee_id=annee_id, semestre_id=semestre_id)


@admin_bp.route('/bulletins/regles', methods=['GET', 'POST'])
@admin_required
def regles_passage():
    annees = AnneeAcademique.query.order_by(AnneeAcademique.libelle.desc()).all()
    if request.method == 'POST':
        try:
            annee_id = int(request.form['annee_academique_id'])
            moyenne_min = float(request.form.get('moyenne_min', '10'))
            credits_min = float(request.form.get('credits_min', '0'))
            if not (0 <= moyenne_min <= 20 and credits_min >= 0):
                raise ValueError
            regle = ReglePassage.query.filter_by(annee_academique_id=annee_id).first()
            if regle is None:
                regle = ReglePassage(annee_academique_id=annee_id)
                db.session.add(regle)
            regle.moyenne_min = moyenne_min
            regle.credits_min = credits_min
            regle.compensation_autorisee = bool(request.form.get('compensation_autorisee'))
            if _commit_or_error('Règle académique enregistrée.'):
                return redirect(url_for('admin.regles_passage'))
        except (ValueError, KeyError):
            db.session.rollback()
            flash('Paramètres de passage invalides.', 'error')
    regles = ReglePassage.query.order_by(ReglePassage.id.desc()).all()
    return render_template('admin/regles_passage.html', annees=annees, regles=regles)


@admin_bp.route('/bulletins/<int:inscription_id>/<int:semestre_id>/publier', methods=['POST'])
@admin_required
def publier_bulletin(inscription_id, semestre_id):
    inscription = db.session.get(InscriptionEtudiant, inscription_id)
    semestre = db.session.get(Semestre, semestre_id)
    if not inscription or not semestre:
        flash('Bulletin introuvable.', 'error')
        return redirect(url_for('admin.bulletins'))
    data = _calculer_bulletin(inscription, semestre)
    if not data:
        flash('Aucun résultat publié pour ce semestre.', 'error')
        return redirect(url_for('admin.bulletins'))
    bulletin = BulletinSemestre.query.filter_by(inscription_id=inscription.id, semestre_id=semestre.id).first()
    if bulletin is None:
        bulletin = BulletinSemestre(inscription_id=inscription.id, semestre_id=semestre.id)
        db.session.add(bulletin)
    for key, value in data.items():
        setattr(bulletin, key, value)
    bulletin.publie = True
    if _commit_or_error('Bulletin publié à l’étudiant.'):
        return redirect(url_for('admin.bulletins'))
    return redirect(url_for('admin.bulletins'))
