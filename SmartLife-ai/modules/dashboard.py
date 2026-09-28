from flask import Blueprint, render_template, session, make_response
from datetime import datetime
from sqlalchemy import func
from modules.database import db, Utilisateur, Tache, Depense, Revenu, InscriptionEtudiant, ResultatMatiere, BulletinSemestre, Semestre
from utils.decorators import login_required

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates/dashboard')


@dashboard_bp.route('/')
@login_required
def accueil():
    utilisateur = db.session.get(Utilisateur, session['user_id'])

    debut_mois = datetime.utcnow().replace(day=1)

    nb_taches_en_cours = (
        Tache.query
        .filter_by(user_id=utilisateur.id)
        .filter(Tache.statut != 'termine')
        .count()
    )

    taches = (
        Tache.query
        .filter_by(user_id=utilisateur.id)
        .filter(Tache.statut != 'termine')
        .order_by(Tache.date_limite.asc().nulls_last())
        .limit(5)
        .all()
    )

    total_depenses = db.session.query(func.coalesce(func.sum(Depense.montant), 0.0)).filter(
        Depense.user_id == utilisateur.id, Depense.date >= debut_mois
    ).scalar()

    total_revenus = db.session.query(func.coalesce(func.sum(Revenu.montant), 0.0)).filter(
        Revenu.user_id == utilisateur.id, Revenu.date >= debut_mois
    ).scalar()

    return render_template(
        'dashboard/accueil.html',
        nom=utilisateur.nom,
        nb_taches_en_cours=nb_taches_en_cours,
        taches=taches,
        total_depenses=total_depenses,
        solde=total_revenus - total_depenses,
    )


@dashboard_bp.route('/mon-dossier')
@login_required
def mon_dossier():
    utilisateur = db.session.get(Utilisateur, session['user_id'])
    inscription = (InscriptionEtudiant.query
                   .filter_by(utilisateur_id=utilisateur.id)
                   .order_by(InscriptionEtudiant.date_inscription.desc())
                   .first())
    return render_template('dashboard/mon_dossier.html', utilisateur=utilisateur, inscription=inscription)


@dashboard_bp.route('/mes-resultats')
@login_required
def mes_resultats():
    utilisateur = db.session.get(Utilisateur, session['user_id'])
    inscription = (InscriptionEtudiant.query.filter_by(utilisateur_id=utilisateur.id, statut='actif')
                   .order_by(InscriptionEtudiant.date_inscription.desc()).first())
    resultats = []
    if inscription:
        resultats = (ResultatMatiere.query
                     .filter_by(inscription_id=inscription.id, publie=True)
                     .join(ResultatMatiere.matiere)
                     .join(ResultatMatiere.semestre)
                     .order_by(ResultatMatiere.semestre_id, ResultatMatiere.matiere_id).all())
    return render_template('dashboard/mes_resultats.html', utilisateur=utilisateur, inscription=inscription, resultats=resultats)


@dashboard_bp.route('/mes-bulletins')
@login_required
def mes_bulletins():
    utilisateur = db.session.get(Utilisateur, session['user_id'])
    inscription = (InscriptionEtudiant.query.filter_by(utilisateur_id=utilisateur.id, statut='actif')
                   .order_by(InscriptionEtudiant.date_inscription.desc()).first())
    bulletins = []
    if inscription:
        bulletins = (BulletinSemestre.query.filter_by(inscription_id=inscription.id, publie=True)
                     .join(BulletinSemestre.semestre).order_by(Semestre.ordre).all())
    return render_template('dashboard/mes_bulletins.html', utilisateur=utilisateur, inscription=inscription, bulletins=bulletins)


@dashboard_bp.route('/bulletin/<int:bulletin_id>/pdf')
@login_required
def bulletin_pdf(bulletin_id):
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    utilisateur = db.session.get(Utilisateur, session['user_id'])
    bulletin = db.session.get(BulletinSemestre, bulletin_id)
    if not bulletin or not bulletin.publie or bulletin.inscription.utilisateur_id != utilisateur.id:
        return ('Bulletin introuvable.', 404)

    resultats = (ResultatMatiere.query
                 .filter_by(inscription_id=bulletin.inscription_id, semestre_id=bulletin.semestre_id, publie=True)
                 .join(ResultatMatiere.matiere).order_by(ResultatMatiere.matiere_id).all())
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 55
    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(50, y, 'SmartLife AI — Bulletin de semestre')
    y -= 28
    pdf.setFont('Helvetica', 10)
    pdf.drawString(50, y, f"Étudiant : {utilisateur.nom}")
    y -= 16
    pdf.drawString(50, y, f"Matricule : {bulletin.inscription.matricule}")
    y -= 16
    pdf.drawString(50, y, f"Filière : {bulletin.inscription.filiere.nom} | Niveau : {bulletin.inscription.niveau.nom}")
    y -= 16
    pdf.drawString(50, y, f"Année : {bulletin.inscription.annee_academique.libelle} | {bulletin.semestre.nom}")
    y -= 28
    pdf.setFont('Helvetica-Bold', 9)
    pdf.drawString(50, y, 'Matière')
    pdf.drawString(330, y, 'Coef.')
    pdf.drawString(390, y, 'Note /20')
    pdf.drawString(470, y, 'Statut')
    y -= 16
    pdf.setFont('Helvetica', 9)
    for r in resultats:
        if y < 70:
            pdf.showPage(); y = height - 50
            pdf.setFont('Helvetica', 9)
        pdf.drawString(50, y, f"{r.matiere.code} — {r.matiere.nom}"[:48])
        pdf.drawString(330, y, str(r.matiere.coefficient))
        pdf.drawString(390, y, f"{float(r.note_finale):.2f}")
        pdf.drawString(470, y, 'Validé' if r.valide else 'Non validé')
        y -= 16
    y -= 12
    pdf.setFont('Helvetica-Bold', 10)
    pdf.drawString(50, y, f"Moyenne : {float(bulletin.moyenne):.2f}/20")
    y -= 16
    pdf.drawString(50, y, f"Crédits : {float(bulletin.credits_valides):.2f}/{float(bulletin.total_credits):.2f}")
    y -= 16
    pdf.drawString(50, y, f"Décision : {bulletin.decision}")
    pdf.save()
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=bulletin-{bulletin.inscription.matricule}-{bulletin.semestre.code}.pdf'
    return response
