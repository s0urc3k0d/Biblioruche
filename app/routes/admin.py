from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import BookProposal, VotingSession, VoteOption, Vote, ReadingSession, User, BookReview
from app.forms import ReadingSessionForm, VotingSessionForm, ModerateReviewForm
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Accès réservé aux administrateurs.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Statistiques pour le tableau de bord
    stats = {
        'total_users': User.query.count(),
        'total_proposals': BookProposal.query.count(),
        'pending_proposals': BookProposal.query.filter_by(status='pending').count(),
        'active_votes': VotingSession.query.filter_by(status='active').count(),
        'current_readings': ReadingSession.query.filter_by(status='current').count()
    }
    
    # Propositions récentes
    recent_proposals = BookProposal.query.filter_by(status='pending').order_by(BookProposal.created_at.desc()).limit(10).all()
    
    # Votes actifs
    active_votes = VotingSession.query.filter_by(status='active').all()
    
    # Lectures en cours
    current_readings = ReadingSession.query.filter_by(status='current').all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_proposals=recent_proposals,
                         active_votes=active_votes,
                         current_readings=current_readings)

@admin_bp.route('/proposals')
@login_required
@admin_required
def proposals():
    from flask_wtf import FlaskForm
    status_filter = request.args.get('status', 'pending')
    proposals = BookProposal.query.filter_by(status=status_filter).order_by(BookProposal.created_at.desc()).all()
    form = FlaskForm()  # Formulaire vide pour le token CSRF
    return render_template('admin/proposals.html', proposals=proposals, current_status=status_filter, form=form)

@admin_bp.route('/proposal/<int:proposal_id>/approve')
@login_required
@admin_required
def approve_proposal(proposal_id):
    proposal = BookProposal.query.get_or_404(proposal_id)
    proposal.status = 'approved'
    db.session.commit()
    flash(f'La proposition "{proposal.title}" a été approuvée.', 'success')
    return redirect(url_for('admin.proposals'))

@admin_bp.route('/proposal/<int:proposal_id>/reject')
@login_required
@admin_required
def reject_proposal(proposal_id):
    proposal = BookProposal.query.get_or_404(proposal_id)
    proposal.status = 'rejected'
    db.session.commit()
    flash(f'La proposition "{proposal.title}" a été rejetée.', 'info')
    return redirect(url_for('admin.proposals'))

@admin_bp.route('/proposals/bulk', methods=['POST'])
@login_required
@admin_required
def bulk_proposals():
    """Gérer les actions en lot sur les propositions"""
    action = request.form.get('action')
    proposal_ids = request.form.getlist('proposal_ids')
    
    if not action or not proposal_ids:
        flash('Action ou sélection invalide.', 'error')
        return redirect(url_for('admin.proposals'))
    
    # Valider l'action
    if action not in ['approve', 'reject']:
        flash('Action non autorisée.', 'error')
        return redirect(url_for('admin.proposals'))
    
    # Convertir les IDs en entiers
    try:
        proposal_ids = [int(pid) for pid in proposal_ids]
    except ValueError:
        flash('IDs de propositions invalides.', 'error')
        return redirect(url_for('admin.proposals'))
    
    # Récupérer les propositions
    proposals = BookProposal.query.filter(BookProposal.id.in_(proposal_ids)).all()
    
    if not proposals:
        flash('Aucune proposition trouvée.', 'error')
        return redirect(url_for('admin.proposals'))
    
    # Appliquer l'action
    success_count = 0
    new_status = 'approved' if action == 'approve' else 'rejected'
    
    for proposal in proposals:
        # Vérifier que la proposition est en attente
        if proposal.status == 'pending':
            proposal.status = new_status
            success_count += 1
    
    db.session.commit()
    
    # Message de confirmation
    action_text = 'approuvées' if action == 'approve' else 'rejetées'
    if success_count > 0:
        flash(f'{success_count} proposition(s) {action_text} avec succès.', 'success')
    
    if success_count < len(proposal_ids):
        skipped = len(proposal_ids) - success_count
        flash(f'{skipped} proposition(s) ignorées (déjà traitées).', 'info')
    
    return redirect(url_for('admin.proposals', status='pending'))

@admin_bp.route('/create-vote', methods=['GET', 'POST'])
@login_required
@admin_required
def create_vote():
    form = VotingSessionForm()
    
    if form.validate_on_submit():
        # Ajuster la date de fin pour qu'elle se termine à 23h59 du jour sélectionné
        from datetime import datetime, time
        end_date_with_time = datetime.combine(form.end_date.data, time(23, 59, 59))
        
        voting_session = VotingSession(
            title=form.title.data,
            description=form.description.data,
            end_date=end_date_with_time,
            created_by=current_user.id
        )
        
        db.session.add(voting_session)
        db.session.flush()  # Pour obtenir l'ID de la session de vote
        
        # Ajouter les livres sélectionnés au vote
        selected_books = request.form.getlist('selected_books')
        if not selected_books:
            flash('Veuillez sélectionner au moins un livre pour le vote.', 'error')
            return render_template('admin/create_vote.html', form=form)
        
        for book_id in selected_books:
            vote_option = VoteOption(
                voting_session_id=voting_session.id,
                book_id=int(book_id)
            )
            db.session.add(vote_option)
        
        db.session.commit()
        flash('Session de vote créée avec succès!', 'success')
        return redirect(url_for('admin.votes'))
      # Récupérer les livres approuvés pour la sélection
    approved_books = BookProposal.query.filter_by(status='approved').all()
    
    return render_template('admin/create_vote.html', form=form, approved_books=approved_books)

@admin_bp.route('/votes')
@login_required
@admin_required
def votes():
    active_votes = VotingSession.query.filter_by(status='active').all()
    closed_votes = VotingSession.query.filter_by(status='closed').order_by(VotingSession.end_date.desc()).all()
    
    return render_template('admin/votes.html', active_votes=active_votes, closed_votes=closed_votes)

@admin_bp.route('/vote/<int:vote_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_vote(vote_id):
    from app.forms import EditVotingSessionForm
    from datetime import datetime, time
    
    voting_session = VotingSession.query.get_or_404(vote_id)
    form = EditVotingSessionForm()
    
    if form.validate_on_submit():
        # Ajuster la date de fin pour qu'elle se termine à 23h59 du jour sélectionné
        end_date_with_time = datetime.combine(form.end_date.data, time(23, 59, 59))
        
        voting_session.title = form.title.data
        voting_session.description = form.description.data
        voting_session.end_date = end_date_with_time
        
        db.session.commit()
        flash('Session de vote mise à jour avec succès!', 'success')
        return redirect(url_for('admin.votes'))
    
    if request.method == 'GET':
        form.title.data = voting_session.title
        form.description.data = voting_session.description
        # Convertir la datetime en date pour le formulaire
        form.end_date.data = voting_session.end_date.date() if voting_session.end_date else None
    
    return render_template('admin/edit_vote.html', form=form, voting_session=voting_session)

@admin_bp.route('/vote/<int:vote_id>/close')
@login_required
@admin_required
def close_vote(vote_id):
    voting_session = VotingSession.query.get_or_404(vote_id)
    
    if voting_session.status == 'closed':
        flash('Ce vote est déjà clos.', 'info')
        return redirect(url_for('admin.votes'))
    
    voting_session.status = 'closed'
      # Déterminer les livres gagnants (en cas d'égalité, tous les ex æquo)
    vote_counts = {}
    for option in voting_session.books:
        vote_counts[option.id] = option.get_vote_count()
    
    if vote_counts:
        max_votes = max(vote_counts.values())
        winner_option_ids = [option_id for option_id, count in vote_counts.items() if count == max_votes]
        
        # Si un seul gagnant, définir le winner_book_id
        if len(winner_option_ids) == 1:
            winner_option = VoteOption.query.get(winner_option_ids[0])
            voting_session.winner_book_id = winner_option.book_id
        
        # Marquer tous les livres gagnants comme sélectionnés
        for option_id in winner_option_ids:
            option = VoteOption.query.get(option_id)
            winner_book = BookProposal.query.get(option.book_id)
            winner_book.status = 'selected'
    
    db.session.commit()
    flash('Le vote a été clos et le livre gagnant a été déterminé.', 'success')
    return redirect(url_for('admin.votes'))

@admin_bp.route('/create-reading', methods=['GET', 'POST'])
@login_required
@admin_required
def create_reading():
    form = ReadingSessionForm()
      # Populate choices with selected books
    selected_books = BookProposal.query.filter_by(status='selected').all()
    form.book_id.choices = [(None, 'Sélectionner un livre existant')] + [(book.id, f"{book.title} par {book.author}") for book in selected_books]
    
    if form.validate_on_submit():
        book = None
        
        # Vérifier si on ajoute un nouveau livre ou on utilise un existant
        if form.add_new_book.data and form.new_book_title.data and form.new_book_author.data:            # Créer un nouveau livre
            book = BookProposal(
                title=form.new_book_title.data,
                author=form.new_book_author.data,
                description=form.new_book_description.data,
                isbn=form.new_book_isbn.data,
                publisher=form.new_book_publisher.data,
                publication_year=form.new_book_publication_year.data,
                pages_count=form.new_book_pages_count.data,
                genre=form.new_book_genre.data,
                proposed_by=current_user.id,
                status='selected'  # Directement sélectionné pour la lecture
            )
            db.session.add(book)
            db.session.flush()  # Pour obtenir l'ID
            book_id = book.id
            flash(f'Nouveau livre "{book.title}" ajouté et programmé pour la lecture!', 'success')
        elif form.book_id.data:
            # Utiliser un livre existant
            book_id = form.book_id.data
            book = BookProposal.query.get(book_id)
        else:
            flash('Veuillez sélectionner un livre existant ou ajouter un nouveau livre.', 'error')
            return render_template('admin/create_reading.html', form=form)
        
        reading_session = ReadingSession(
            book_id=book_id,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            debrief_date=form.debrief_date.data,
            description=form.description.data,
            created_by=current_user.id
        )
        
        # Marquer le livre comme en cours de lecture
        if book:
            book.status = 'in_reading'
        
        db.session.add(reading_session)
        db.session.commit()
        
        flash('Session de lecture créée avec succès!', 'success')
        return redirect(url_for('admin.readings'))
    
    return render_template('admin/create_reading.html', form=form)

@admin_bp.route('/readings')
@login_required
@admin_required
def readings():
    current_readings = ReadingSession.query.filter_by(status='current').all()
    upcoming_readings = ReadingSession.query.filter_by(status='upcoming').order_by(ReadingSession.start_date.asc()).all()
    completed_readings = ReadingSession.query.filter_by(status='completed').order_by(ReadingSession.end_date.desc()).all()
    archived_readings = ReadingSession.query.filter_by(status='archived').order_by(ReadingSession.end_date.desc()).all()
    
    return render_template('admin/readings.html',
                         current_readings=current_readings,
                         upcoming_readings=upcoming_readings,
                         completed_readings=completed_readings,
                         archived_readings=archived_readings)

@admin_bp.route('/reading/<int:reading_id>/complete')
@login_required
@admin_required
def complete_reading(reading_id):
    reading_session = ReadingSession.query.get_or_404(reading_id)
    reading_session.status = 'completed'
    
    # Marquer le livre comme terminé
    book = BookProposal.query.get(reading_session.book_id)
    book.status = 'completed'
    
    db.session.commit()
    flash('La session de lecture a été marquée comme terminée.', 'success')
    return redirect(url_for('admin.readings'))

@admin_bp.route('/reading/<int:reading_id>/archive')
@login_required
@admin_required
def archive_reading(reading_id):
    reading_session = ReadingSession.query.get_or_404(reading_id)
    reading_session.status = 'archived'
    
    # Marquer le livre comme archivé
    book = BookProposal.query.get(reading_session.book_id)
    book.status = 'archived'
    
    db.session.commit()
    flash('La session de lecture a été archivée.', 'success')
    return redirect(url_for('admin.readings'))

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/user/<int:user_id>/toggle-admin')
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Vous ne pouvez pas modifier vos propres droits d\'administration.', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'administrateur' if user.is_admin else 'utilisateur normal'
    flash(f'{user.display_name} est maintenant {status}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/reading/<int:reading_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_reading(reading_id):
    from app.forms import EditReadingSessionForm
    reading_session = ReadingSession.query.get_or_404(reading_id)
    form = EditReadingSessionForm()
    
    if form.validate_on_submit():
        reading_session.start_date = form.start_date.data
        reading_session.end_date = form.end_date.data
        reading_session.debrief_date = form.debrief_date.data
        reading_session.description = form.description.data
        
        # Mettre à jour automatiquement le statut basé sur les nouvelles dates
        update_reading_status(reading_session)
        
        db.session.commit()
        flash('Session de lecture mise à jour avec succès!', 'success')
        return redirect(url_for('admin.readings'))
    
    if request.method == 'GET':
        form.start_date.data = reading_session.start_date.date() if reading_session.start_date else None
        form.end_date.data = reading_session.end_date.date() if reading_session.end_date else None
        form.debrief_date.data = reading_session.debrief_date.date() if reading_session.debrief_date else None
        form.description.data = reading_session.description
    
    return render_template('admin/edit_reading.html', form=form, reading=reading_session)

def update_reading_status(reading_session):
    """Met à jour automatiquement le statut d'une session de lecture basé sur la date actuelle"""
    from datetime import date
    today = date.today()
    
    # Convertir les dates en objets date si ce sont des datetime
    start_date = reading_session.start_date.date() if hasattr(reading_session.start_date, 'date') else reading_session.start_date
    end_date = reading_session.end_date.date() if hasattr(reading_session.end_date, 'date') else reading_session.end_date
    
    # Ne pas changer le statut si la lecture est déjà terminée ou archivée
    if reading_session.status in ['completed', 'archived']:
        return
    
    if start_date > today:
        reading_session.status = 'upcoming'
    elif start_date <= today <= end_date:
        reading_session.status = 'current'
    elif end_date < today:
        reading_session.status = 'completed'

@admin_bp.route('/readings/update-statuses')
@login_required
@admin_required
def update_all_reading_statuses():
    """Route pour mettre à jour manuellement tous les statuts des sessions de lecture"""
    readings = ReadingSession.query.filter(ReadingSession.status.in_(['upcoming', 'current'])).all()
    updated_count = 0
    
    for reading in readings:
        old_status = reading.status
        update_reading_status(reading)
        if reading.status != old_status:
            updated_count += 1
    
    db.session.commit()
    flash(f'{updated_count} session(s) de lecture mise(s) à jour.', 'success')
    return redirect(url_for('admin.readings'))

@admin_bp.route('/reading/<int:reading_id>/start')
@login_required
@admin_required
def start_reading(reading_id):
    reading_session = ReadingSession.query.get_or_404(reading_id)
    reading_session.status = 'current'
    
    # Mettre à jour la date de début à aujourd'hui si nécessaire
    if reading_session.start_date.date() > datetime.now().date():
        reading_session.start_date = datetime.now()
    
    # Marquer le livre comme en cours de lecture
    book = BookProposal.query.get(reading_session.book_id)
    book.status = 'in_reading'
    
    db.session.commit()
    flash('La lecture a été démarrée.', 'success')
    return redirect(url_for('admin.readings'))

@admin_bp.route('/reading/<int:reading_id>/delete')
@login_required
@admin_required
def delete_reading(reading_id):
    reading_session = ReadingSession.query.get_or_404(reading_id)
    
    # Remettre le livre en statut 'selected' s'il n'est pas encore en cours
    if reading_session.status == 'upcoming':
        book = BookProposal.query.get(reading_session.book_id)
        book.status = 'selected'
    
    db.session.delete(reading_session)
    db.session.commit()
    flash('La session de lecture a été supprimée.', 'success')
    return redirect(url_for('admin.readings'))

@admin_bp.route('/cleanup-database')
@login_required
@admin_required
def cleanup_database():
    """Nettoyage simple de la base de données"""
    try:
        # Compter avant nettoyage
        rejected_books = BookProposal.query.filter_by(status='rejected').all()
        closed_sessions = VotingSession.query.filter_by(status='closed').all()
        
        votes_count = 0
        for session in closed_sessions:
            votes_count += Vote.query.filter_by(voting_session_id=session.id).count()
        
        # Supprimer les livres rejetés
        for book in rejected_books:
            db.session.delete(book)
        
        # Supprimer les votes et sessions fermées
        for session in closed_sessions:
            # Supprimer les votes
            votes = Vote.query.filter_by(voting_session_id=session.id).all()
            for vote in votes:
                db.session.delete(vote)
            
            # Supprimer les options
            options = VoteOption.query.filter_by(voting_session_id=session.id).all()
            for option in options:
                db.session.delete(option)
            
            # Supprimer la session
            db.session.delete(session)
        
        db.session.commit()
        
        flash(f'Nettoyage terminé: {len(rejected_books)} livres rejetés, {len(closed_sessions)} sessions fermées et {votes_count} votes supprimés.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors du nettoyage: {e}', 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/reviews')
@login_required
@admin_required
def reviews():
    """List all reviews for moderation"""
    page = request.args.get('page', 1, type=int)
    reviews = BookReview.query.order_by(BookReview.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/reviews.html', reviews=reviews)

@admin_bp.route('/reviews/<int:review_id>/moderate', methods=['GET', 'POST'])
@login_required
@admin_required
def moderate_review(review_id):
    """Moderate a specific review"""
    review = BookReview.query.get_or_404(review_id)
    form = ModerateReviewForm()
    
    if request.method == 'GET':
        form.is_visible.data = review.is_visible
        form.is_moderated.data = review.is_moderated
    
    if form.validate_on_submit():
        review.is_visible = form.is_visible.data
        review.is_moderated = form.is_moderated.data
        db.session.commit()
        
        action = "visible" if review.is_visible else "masqué"
        flash(f'Avis {action} avec succès!', 'success')
        return redirect(url_for('admin.reviews'))
    
    return render_template('admin/moderate_review.html', form=form, review=review)
