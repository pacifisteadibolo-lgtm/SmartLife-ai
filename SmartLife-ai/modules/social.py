from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from modules.database import db, Publication, Commentaire, Utilisateur
from utils.decorators import login_required
from utils.fichiers import enregistrer_fichier, type_publication_pour

social_bp = Blueprint('social', __name__, template_folder='../templates/social')


@social_bp.route('/')
@login_required
def feed():
    publications = (
        Publication.query
        .order_by(Publication.date.desc())
        .limit(30)
        .all()
    )
    tous_les_etudiants = (
        Utilisateur.query
        .filter(Utilisateur.id != session['user_id'])
        .order_by(Utilisateur.nom)
        .limit(12)
        .all()
    )
    return render_template('social/feed.html', publications=publications, tous_les_etudiants=tous_les_etudiants)


@social_bp.route('/publier', methods=['POST'])
@login_required
def publier():
    contenu = request.form.get('contenu', '').strip()
    fichier_uploade = request.files.get('fichier')

    if len(contenu) > 2000:
        flash("Message trop long (2000 caractères max).", 'error')
        return redirect(url_for('social.feed'))

    publication = Publication(user_id=session['user_id'], contenu=contenu or None, type='texte')
    db.session.add(publication)
    db.session.flush()  # récupère publication.id avant de lier le fichier

    fichier = None
    if fichier_uploade and fichier_uploade.filename:
        fichier = enregistrer_fichier(fichier_uploade, session['user_id'], pub_id=publication.id)
        if fichier is None:
            db.session.rollback()
            flash("Format de fichier non autorisé.", 'error')
            return redirect(url_for('social.feed'))
        publication.type = type_publication_pour(fichier)

    if not contenu and not fichier:
        db.session.rollback()
        flash("Le message ne peut pas être vide.", 'error')
        return redirect(url_for('social.feed'))

    db.session.commit()
    flash("Publié !", 'success')
    return redirect(url_for('social.feed'))


@social_bp.route('/<int:pub_id>/liker', methods=['POST'])
@login_required
def liker(pub_id):
    publication = Publication.query.get_or_404(pub_id)
    publication.likes = (publication.likes or 0) + 1
    db.session.commit()
    return redirect(url_for('social.feed'))


@social_bp.route('/<int:pub_id>/commenter', methods=['POST'])
@login_required
def commenter(pub_id):
    publication = Publication.query.get_or_404(pub_id)
    contenu = request.form.get('contenu', '').strip()

    if not contenu:
        flash("Le commentaire ne peut pas être vide.", 'error')
        return redirect(url_for('social.feed'))

    commentaire = Commentaire(pub_id=publication.id, user_id=session['user_id'], contenu=contenu)
    db.session.add(commentaire)
    db.session.commit()
    return redirect(url_for('social.feed'))


@social_bp.route('/<int:pub_id>/supprimer', methods=['POST'])
@login_required
def supprimer(pub_id):
    publication = Publication.query.filter_by(id=pub_id, user_id=session['user_id']).first_or_404()
    db.session.delete(publication)
    db.session.commit()
    flash("Publication supprimée.", 'success')
    return redirect(url_for('social.feed'))
