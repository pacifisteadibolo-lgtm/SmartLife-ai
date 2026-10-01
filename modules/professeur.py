from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from modules.database import db, Utilisateur, Professeur, Matiere, EvaluationType, NoteEvaluation, ResultatMatiere, InscriptionEtudiant
from utils.decorators import professeur_required

professeur_bp = Blueprint('professeur', __name__, template_folder='../templates/professeur')


def _calculer_note_finale(matiere, inscription):
    types = (EvaluationType.query.filter_by(matiere_id=matiere.id, active=True)
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
        valeur, sur = float(n.note), float(t.note_sur)
        if sur <= 0 or valeur < 0 or valeur > sur:
            return None
        total += (valeur / sur) * 20.0 * float(t.poids)
    return round(total / total_poids, 2)


def _professeur_courant():
    return Professeur.query.filter_by(utilisateur_id=session['user_id'], actif=True).first()


@professeur_bp.route('/')
@professeur_required
def accueil():
    professeur = _professeur_courant()
    if not professeur:
        flash('Ton profil professeur n’est pas encore associé à ton compte.', 'error')
        return redirect(url_for('dashboard.accueil'))
    matieres = Matiere.query.filter_by(professeur_id=professeur.id, active=True).all()
    return render_template('professeur/dashboard.html', professeur=professeur, matieres=matieres)


@professeur_bp.route('/matiere/<int:matiere_id>', methods=['GET', 'POST'])
@professeur_required
def matiere(matiere_id):
    professeur = _professeur_courant()
    matiere = Matiere.query.filter_by(id=matiere_id, professeur_id=professeur.id, active=True).first()
    if not matiere:
        flash('Cette matière ne t’est pas attribuée.', 'error')
        return redirect(url_for('professeur.accueil'))

    types = EvaluationType.query.filter_by(matiere_id=matiere.id, active=True).order_by(EvaluationType.ordre, EvaluationType.id).all()
    inscriptions = (InscriptionEtudiant.query.filter_by(niveau_id=matiere.niveau_id, statut='actif')
                    .join(Utilisateur).order_by(Utilisateur.nom).all())

    if request.method == 'POST':
        action = request.form.get('action')
        try:
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
                    note.saisi_par_id = session['user_id']

                final = _calculer_note_finale(matiere, inscription)
                if final is not None:
                    resultat = ResultatMatiere.query.filter_by(inscription_id=inscription.id, matiere_id=matiere.id).first()
                    if resultat is None:
                        resultat = ResultatMatiere(inscription_id=inscription.id, matiere_id=matiere.id, semestre_id=matiere.semestre_id)
                        db.session.add(resultat)
                    resultat.note_finale = final
                    resultat.moyenne_sur = 20
                    resultat.valide = final >= float(matiere.seuil_validation)
                    if action == 'soumettre':
                        resultat.statut = 'soumis'
                        resultat.soumis_le = datetime.utcnow()
            db.session.commit()
            flash('Notes enregistrées.' if action != 'soumettre' else 'Notes soumises à l’administration pour validation.', 'success')
            return redirect(url_for('professeur.matiere', matiere_id=matiere.id))
        except (ValueError, TypeError):
            db.session.rollback()
            flash('Une note est invalide.', 'error')

    notes = NoteEvaluation.query.filter(NoteEvaluation.inscription_id.in_([i.id for i in inscriptions])).all() if inscriptions else []
    notes_map = {(n.inscription_id, n.evaluation_type_id): n for n in notes}
    resultats = ResultatMatiere.query.filter(ResultatMatiere.matiere_id == matiere.id,
                                              ResultatMatiere.inscription_id.in_([i.id for i in inscriptions])).all() if inscriptions else []
    resultats_map = {r.inscription_id: r for r in resultats}
    return render_template('professeur/matiere.html', professeur=professeur, matiere=matiere, types=types,
                           inscriptions=inscriptions, notes_map=notes_map, resultats_map=resultats_map)
