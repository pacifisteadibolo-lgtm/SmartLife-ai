from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy import func

from modules.database import (
    db, Utilisateur, Filiere, Niveau, AnneeAcademique, Semestre,
    InscriptionEtudiant, Matiere, ResultatMatiere, BulletinSemestre,
    Notification, AnnonceAcademique, EvenementAcademique, JournalAudit,
)
from utils.decorators import admin_required, login_required

admin_plus_bp = Blueprint('admin_plus', __name__)
academique_bp = Blueprint('academique', __name__)


def _utilisateurs_cibles(target_type, target_id=None):
    if target_type == 'tous':
        return Utilisateur.query.filter_by(statut='actif').all()
    if target_type == 'etudiants':
        return Utilisateur.query.filter_by(role='etudiant', statut='actif').all()
    if target_type == 'professeurs':
        return Utilisateur.query.filter_by(role='professeur', statut='actif').all()
    if target_type == 'filiere' and target_id:
        ids = (db.session.query(InscriptionEtudiant.utilisateur_id)
               .filter(InscriptionEtudiant.filiere_id == int(target_id), InscriptionEtudiant.statut == 'actif')
               .distinct().all())
        return Utilisateur.query.filter(Utilisateur.id.in_([x[0] for x in ids]), Utilisateur.statut == 'actif').all() if ids else []
    if target_type == 'niveau' and target_id:
        ids = (db.session.query(InscriptionEtudiant.utilisateur_id)
               .filter(InscriptionEtudiant.niveau_id == int(target_id), InscriptionEtudiant.statut == 'actif')
               .distinct().all())
        return Utilisateur.query.filter(Utilisateur.id.in_([x[0] for x in ids]), Utilisateur.statut == 'actif').all() if ids else []
    return []


def _notifier_utilisateurs(utilisateurs, type_, message, lien=None):
    for user in utilisateurs:
        db.session.add(Notification(user_id=user.id, type=type_, message=message, lien=lien))


@admin_plus_bp.route('/annonces', methods=['GET', 'POST'])
@admin_required
def annonces():
    if request.method == 'POST':
        titre = request.form.get('titre', '').strip()
        contenu = request.form.get('contenu', '').strip()
        target_type = request.form.get('target_type', 'tous')
        target_id = request.form.get('target_id', type=int)
        if not titre or not contenu or target_type not in {'tous', 'etudiants', 'professeurs', 'filiere', 'niveau'}:
            flash('Titre, contenu ou ciblage invalide.', 'error')
        else:
            annonce = AnnonceAcademique(
                titre=titre, contenu=contenu, target_type=target_type,
                target_id=target_id if target_type in {'filiere', 'niveau'} else None,
                publie=True, publie_le=datetime.utcnow(), auteur_id=session['user_id']
            )
            db.session.add(annonce)
            db.session.flush()
            cibles = _utilisateurs_cibles(target_type, target_id)
            _notifier_utilisateurs(cibles, 'annonce_academique', titre, '/academique/annonces')
            db.session.commit()
            flash(f'Annonce publiée à {len(cibles)} utilisateur(s).', 'success')
            return redirect(url_for('admin_plus.annonces'))
    annonces = AnnonceAcademique.query.order_by(AnnonceAcademique.created_at.desc()).all()
    filieres = Filiere.query.filter_by(active=True).order_by(Filiere.nom).all()
    niveaux = Niveau.query.filter_by(active=True).order_by(Niveau.nom).all()
    return render_template('admin/annonces.html', annonces=annonces, filieres=filieres, niveaux=niveaux)


@admin_plus_bp.route('/annonces/<int:annonce_id>/supprimer', methods=['POST'])
@admin_required
def supprimer_annonce(annonce_id):
    annonce = db.session.get(AnnonceAcademique, annonce_id)
    if annonce:
        db.session.delete(annonce)
        db.session.commit()
        flash('Annonce supprimée.', 'success')
    return redirect(url_for('admin_plus.annonces'))


@admin_plus_bp.route('/evenements', methods=['GET', 'POST'])
@admin_required
def evenements():
    if request.method == 'POST':
        titre = request.form.get('titre', '').strip()
        description = request.form.get('description', '').strip() or None
        type_evenement = request.form.get('type_evenement', 'autre')
        debut_raw = request.form.get('debut', '')
        fin_raw = request.form.get('fin', '')
        try:
            debut = datetime.fromisoformat(debut_raw)
            fin = datetime.fromisoformat(fin_raw) if fin_raw else None
        except ValueError:
            debut, fin = None, None
        if not titre or not debut:
            flash('Le titre et la date de début sont obligatoires.', 'error')
        else:
            evenement = EvenementAcademique(
                titre=titre, description=description, type_evenement=type_evenement,
                debut=debut, fin=fin, lieu=request.form.get('lieu', '').strip() or None,
                created_by_id=session['user_id']
            )
            db.session.add(evenement)
            db.session.flush()
            cibles = Utilisateur.query.filter_by(statut='actif').all()
            _notifier_utilisateurs(cibles, 'evenement_academique', titre, '/academique/calendrier')
            db.session.commit()
            flash('Événement académique ajouté et notifié.', 'success')
            return redirect(url_for('admin_plus.evenements'))
    evenements = EvenementAcademique.query.order_by(EvenementAcademique.debut.desc()).all()
    return render_template('admin/evenements.html', evenements=evenements)


@admin_plus_bp.route('/evenements/<int:evenement_id>/supprimer', methods=['POST'])
@admin_required
def supprimer_evenement(evenement_id):
    evenement = db.session.get(EvenementAcademique, evenement_id)
    if evenement:
        db.session.delete(evenement)
        db.session.commit()
        flash('Événement supprimé.', 'success')
    return redirect(url_for('admin_plus.evenements'))


@admin_plus_bp.route('/analytics')
@admin_required
def analytics():
    annee_id = request.args.get('annee_id', type=int)
    filiere_id = request.args.get('filiere_id', type=int)
    niveau_id = request.args.get('niveau_id', type=int)
    semestre_id = request.args.get('semestre_id', type=int)

    inscriptions_q = InscriptionEtudiant.query.filter_by(statut='actif')
    if annee_id:
        inscriptions_q = inscriptions_q.filter_by(annee_academique_id=annee_id)
    if filiere_id:
        inscriptions_q = inscriptions_q.filter_by(filiere_id=filiere_id)
    if niveau_id:
        inscriptions_q = inscriptions_q.filter_by(niveau_id=niveau_id)
    inscriptions = inscriptions_q.all()
    inscription_ids = [i.id for i in inscriptions]

    resultats = []
    if inscription_ids:
        rq = ResultatMatiere.query.filter(ResultatMatiere.inscription_id.in_(inscription_ids), ResultatMatiere.publie.is_(True))
        if semestre_id:
            rq = rq.filter_by(semestre_id=semestre_id)
        resultats = rq.all()

    notes = [float(r.note_finale) for r in resultats if r.note_finale is not None]
    valides = sum(1 for r in resultats if r.valide)
    credits_total = round(sum(float(r.matiere.credits) for r in resultats), 2)
    credits_valides = round(sum(float(r.matiere.credits) for r in resultats if r.valide), 2)
    moyenne = round(sum(notes) / len(notes), 2) if notes else 0
    taux = round(valides / len(resultats) * 100, 1) if resultats else 0

    par_matiere = {}
    for r in resultats:
        key = r.matiere.nom
        row = par_matiere.setdefault(key, {'matiere': key, 'notes': [], 'valides': 0, 'total': 0})
        if r.note_finale is not None:
            row['notes'].append(float(r.note_finale))
        row['valides'] += int(bool(r.valide))
        row['total'] += 1
    for row in par_matiere.values():
        row['moyenne'] = round(sum(row['notes']) / len(row['notes']), 2) if row['notes'] else 0
        row['taux'] = round(row['valides'] / row['total'] * 100, 1) if row['total'] else 0

    par_filiere = {}
    for r in resultats:
        f = r.inscription.filiere.nom
        row = par_filiere.setdefault(f, {'filiere': f, 'notes': [], 'valides': 0, 'total': 0})
        if r.note_finale is not None:
            row['notes'].append(float(r.note_finale))
        row['valides'] += int(bool(r.valide))
        row['total'] += 1
    for row in par_filiere.values():
        row['moyenne'] = round(sum(row['notes']) / len(row['notes']), 2) if row['notes'] else 0
        row['taux'] = round(row['valides'] / row['total'] * 100, 1) if row['total'] else 0

    par_niveau = {}
    for r in resultats:
        n = r.inscription.niveau.nom
        row = par_niveau.setdefault(n, {'niveau': n, 'notes': [], 'valides': 0, 'total': 0})
        if r.note_finale is not None:
            row['notes'].append(float(r.note_finale))
        row['valides'] += int(bool(r.valide))
        row['total'] += 1
    for row in par_niveau.values():
        row['moyenne'] = round(sum(row['notes']) / len(row['notes']), 2) if row['notes'] else 0
        row['taux'] = round(row['valides'] / row['total'] * 100, 1) if row['total'] else 0

    return render_template('admin/analytics.html',
                           annees=AnneeAcademique.query.order_by(AnneeAcademique.libelle.desc()).all(),
                           filieres=Filiere.query.filter_by(active=True).order_by(Filiere.nom).all(),
                           niveaux=Niveau.query.filter_by(active=True).order_by(Niveau.nom).all(),
                           semestres=Semestre.query.order_by(Semestre.ordre).all(),
                           annee_id=annee_id, filiere_id=filiere_id, niveau_id=niveau_id, semestre_id=semestre_id,
                           total_etudiants=len(inscriptions), total_resultats=len(resultats), moyenne=moyenne,
                           taux_validation=taux, credits_total=credits_total, credits_valides=credits_valides,
                           par_matiere=sorted(par_matiere.values(), key=lambda x: x['matiere']),
                           par_filiere=sorted(par_filiere.values(), key=lambda x: x['filiere']),
                           par_niveau=sorted(par_niveau.values(), key=lambda x: x['niveau']))


@admin_plus_bp.route('/audit')
@admin_required
def audit():
    logs = JournalAudit.query.order_by(JournalAudit.created_at.desc()).limit(300).all()
    return render_template('admin/audit.html', logs=logs)


@academique_bp.route('/annonces')
@login_required
def annonces_publiques():
    user = db.session.get(Utilisateur, session['user_id'])
    annonces = AnnonceAcademique.query.filter_by(publie=True).order_by(AnnonceAcademique.created_at.desc()).all()
    visibles = []
    inscription = (InscriptionEtudiant.query.filter_by(utilisateur_id=user.id, statut='actif')
                   .order_by(InscriptionEtudiant.date_inscription.desc()).first())
    for a in annonces:
        if a.target_type == 'tous': ok = True
        elif a.target_type == 'etudiants': ok = user.role == 'etudiant'
        elif a.target_type == 'professeurs': ok = user.role == 'professeur'
        elif a.target_type == 'filiere': ok = bool(inscription and inscription.filiere_id == a.target_id)
        elif a.target_type == 'niveau': ok = bool(inscription and inscription.niveau_id == a.target_id)
        else: ok = False
        if ok: visibles.append(a)
    return render_template('academique/annonces.html', annonces=visibles)


@academique_bp.route('/calendrier')
@login_required
def calendrier():
    evenements = EvenementAcademique.query.order_by(EvenementAcademique.debut.asc()).all()
    return render_template('academique/calendrier.html', evenements=evenements)


@academique_bp.route('/notifications')
@login_required
def notifications():
    user_id = session['user_id']
    items = Notification.query.filter_by(user_id=user_id).order_by(Notification.date.desc()).limit(100).all()
    return render_template('academique/notifications.html', notifications=items)


@academique_bp.route('/notifications/<int:notification_id>/lue', methods=['POST'])
@login_required
def notification_lue(notification_id):
    item = Notification.query.filter_by(id=notification_id, user_id=session['user_id']).first()
    if item:
        item.lu = True
        db.session.commit()
    return redirect(url_for('academique.notifications'))
