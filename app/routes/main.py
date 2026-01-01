from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db, limiter
from app.models import BookProposal, VotingSession, VoteOption, Vote, ReadingSession, User, BookReview, ReadingParticipation, Badge, UserBadge
from app.badge_manager import BadgeManager
from app.forms import BookProposalForm, VoteForm, BookReviewForm
from datetime import datetime
import bleach

main_bp = Blueprint('main', __name__)

def sanitize_input(text):
    """Nettoyer les entrées utilisateur pour éviter les injections XSS"""
    if text is None:
        return None
    return bleach.clean(text, strip=True)


@main_bp.route('/health')
def health_check():
    """Endpoint de health check pour Docker/monitoring"""
    try:
        # Vérifier la connexion à la DB
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


@main_bp.route('/')
def index():
    # Récupérer les informations pour la page d'accueil
    current_reading = ReadingSession.query.filter_by(status='current').first()
    upcoming_reading = ReadingSession.query.filter_by(status='upcoming').order_by(ReadingSession.start_date.asc()).first()
    active_vote = VotingSession.query.filter_by(status='active').first()
    
    recent_proposals = BookProposal.query.filter_by(status='pending').order_by(BookProposal.created_at.desc()).limit(5).all()
    
    return render_template('index.html', 
                         current_reading=current_reading,
                         upcoming_reading=upcoming_reading,
                         active_vote=active_vote,
                         recent_proposals=recent_proposals)

@main_bp.route('/propose-book', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per hour", methods=["POST"])  # Limite à 5 propositions par heure
def propose_book():
    form = BookProposalForm()
    
    if form.validate_on_submit():
        book_proposal = BookProposal(
            title=sanitize_input(form.title.data),
            author=sanitize_input(form.author.data),
            description=sanitize_input(form.description.data),
            isbn=sanitize_input(form.isbn.data),
            publisher=sanitize_input(form.publisher.data),
            publication_year=form.publication_year.data,
            pages_count=form.pages_count.data,
            genre=sanitize_input(form.genre.data),
            proposed_by=current_user.id
        )
        db.session.add(book_proposal)
        db.session.commit()
        
        # Vérifier et attribuer des badges automatiquement
        awarded_badges = BadgeManager.check_and_award_badges(current_user.id)
        if awarded_badges:
            badge_names = [badge.name for badge in awarded_badges]
            flash(f'🏆 Félicitations ! Vous avez gagné le(s) badge(s) : {", ".join(badge_names)}', 'success')
        
        flash('Votre proposition de livre a été soumise avec succès !', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('propose_book.html', form=form)

@main_bp.route('/books')
def books():
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Nombre de livres par page
    status_filter = request.args.get('status', 'all')
    
    # Paramètres de recherche avancée
    search_query = request.args.get('q', '').strip()
    genre_filter = request.args.get('genre', '').strip()
    year_filter = request.args.get('year', '', type=str).strip()
    sort_by = request.args.get('sort', 'recent')
    
    # Construire la requête de base
    query = BookProposal.query
    
    if status_filter == 'pending':
        query = query.filter_by(status='pending')
    elif status_filter == 'approved':
        query = query.filter_by(status='approved')
    elif status_filter == 'selected':
        query = query.filter(BookProposal.status.in_(['selected', 'in_reading']))
    elif status_filter == 'completed':
        query = query.filter_by(status='completed')
    elif status_filter == 'archived':
        query = query.filter_by(status='archived')
    
    # Appliquer la recherche textuelle
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            db.or_(
                BookProposal.title.ilike(search_pattern),
                BookProposal.author.ilike(search_pattern),
                BookProposal.description.ilike(search_pattern)
            )
        )
    
    # Filtrer par genre
    if genre_filter:
        query = query.filter(BookProposal.genre == genre_filter)
    
    # Filtrer par année
    if year_filter:
        try:
            query = query.filter(BookProposal.publication_year == int(year_filter))
        except ValueError:
            pass
    
    # Tri
    if sort_by == 'title':
        query = query.order_by(BookProposal.title.asc())
    elif sort_by == 'author':
        query = query.order_by(BookProposal.author.asc())
    elif sort_by == 'rating':
        # On ne peut pas trier par rating calculé directement, on garde recent
        query = query.order_by(BookProposal.created_at.desc())
    else:  # recent (default)
        query = query.order_by(BookProposal.created_at.desc())
    
    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Compter les livres par statut pour les badges
    counts = {
        'all': BookProposal.query.count(),
        'pending': BookProposal.query.filter_by(status='pending').count(),
        'approved': BookProposal.query.filter_by(status='approved').count(),
        'selected': BookProposal.query.filter(BookProposal.status.in_(['selected', 'in_reading'])).count(),
        'completed': BookProposal.query.filter_by(status='completed').count(),
        'archived': BookProposal.query.filter_by(status='archived').count(),
    }
    
    # Récupérer les genres et années disponibles pour les filtres
    genres = db.session.query(BookProposal.genre).filter(
        BookProposal.genre != None,
        BookProposal.genre != ''
    ).distinct().order_by(BookProposal.genre).all()
    genres = [g[0] for g in genres]
    
    years = db.session.query(BookProposal.publication_year).filter(
        BookProposal.publication_year != None
    ).distinct().order_by(BookProposal.publication_year.desc()).all()
    years = [y[0] for y in years]
    
    return render_template('books.html', 
                         pagination=pagination,
                         books=pagination.items,
                         current_status=status_filter,
                         counts=counts,
                         genres=genres,
                         years=years)

@main_bp.route('/vote/<int:vote_id>')
def vote_detail(vote_id):
    voting_session = VotingSession.query.get_or_404(vote_id)
    
    # Récupérer tous les votes de l'utilisateur pour cette session
    user_votes = []
    if current_user.is_authenticated:
        user_votes = Vote.query.filter_by(user_id=current_user.id, voting_session_id=vote_id).all()
    
    form = VoteForm()
    form.vote_option_ids.choices = [(option.id, f"{option.book.title} par {option.book.author}") 
                                   for option in voting_session.books]
    
    # Pré-remplir le formulaire avec les votes existants
    if user_votes:
        form.vote_option_ids.data = [vote.vote_option_id for vote in user_votes]    # Afficher les résultats si:
    # 1. L'utilisateur a voté 
    # 2. Le vote est clos
    # 3. Admin qui demande explicitement à voir les résultats (paramètre show_results)
    show_results = (len(user_votes) > 0 or 
                   voting_session.status == 'closed' or 
                   (current_user.is_authenticated and current_user.is_admin and request.args.get('show_results')))
    
    results = []
    
    if show_results:
        total_votes = Vote.query.filter_by(voting_session_id=vote_id).count()
        for option in voting_session.books:
            vote_count = option.get_vote_count()
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
              # Récupérer les votants pour les admins
            voters = []
            if current_user.is_authenticated and current_user.is_admin:
                option_votes = Vote.query.filter_by(
                    voting_session_id=vote_id,
                    vote_option_id=option.id
                ).all()
                voters = [vote.voter for vote in option_votes]
            
            results.append({
                'option': option,
                'count': vote_count,
                'percentage': percentage,
                'voters': voters
            })
        results.sort(key=lambda x: x['count'], reverse=True)
    
    return render_template('vote_detail_new.html', 
                         voting_session=voting_session, 
                         form=form,
                         user_votes=user_votes,
                         show_results=show_results,
                         results=results)

@main_bp.route('/vote/<int:vote_id>/submit', methods=['POST'])
@login_required
def submit_vote(vote_id):
    voting_session = VotingSession.query.get_or_404(vote_id)
    
    if voting_session.status != 'active':
        flash('Ce vote n\'est plus actif.', 'error')
        return redirect(url_for('main.vote_detail', vote_id=vote_id))
    
    if datetime.now() > voting_session.end_date:
        flash('Ce vote a expiré.', 'error')
        return redirect(url_for('main.vote_detail', vote_id=vote_id))
    
    form = VoteForm()
    form.vote_option_ids.choices = [(option.id, f"{option.book.title} par {option.book.author}") 
                                   for option in voting_session.books]
    
    if form.validate_on_submit():
        # Supprimer tous les votes existants de l'utilisateur pour cette session
        existing_votes = Vote.query.filter_by(
            user_id=current_user.id,
            voting_session_id=vote_id
        ).all()
        
        for vote in existing_votes:
            db.session.delete(vote)
          # Créer les nouveaux votes
        for option_id in form.vote_option_ids.data:
            new_vote = Vote(
                user_id=current_user.id,
                voting_session_id=vote_id,
                vote_option_id=option_id
            )
            db.session.add(new_vote)
        
        db.session.commit()
        
        # Vérifier et attribuer des badges pour les votes
        awarded_badges = BadgeManager.check_and_award_badges(current_user.id)
        if awarded_badges:
            badge_names = [badge.name for badge in awarded_badges]
            flash(f'🏆 Félicitations ! Vous avez gagné le(s) badge(s) : {", ".join(badge_names)}', 'success')
        
        vote_count = len(form.vote_option_ids.data)
        if vote_count == 1:
            flash('Votre vote a été enregistré!', 'success')
        else:
            flash(f'Vos {vote_count} votes ont été enregistrés!', 'success')
    else:
        flash('Erreur lors de l\'enregistrement de votre vote.', 'error')
    
    return redirect(url_for('main.vote_detail', vote_id=vote_id))

@main_bp.route('/readings')
def readings():
    current_readings = ReadingSession.query.filter_by(status='current').all()
    upcoming_readings = ReadingSession.query.filter_by(status='upcoming').order_by(ReadingSession.start_date.asc()).all()
    completed_readings = ReadingSession.query.filter_by(status='completed').order_by(ReadingSession.end_date.desc()).limit(10).all()
    archived_readings = ReadingSession.query.filter_by(status='archived').order_by(ReadingSession.end_date.desc()).all()
    
    return render_template('readings.html',
                         current_readings=current_readings,
                         upcoming_readings=upcoming_readings,
                         completed_readings=completed_readings,
                         archived_readings=archived_readings)

@main_bp.route('/book/<int:book_id>')
def book_detail(book_id):
    book = BookProposal.query.get_or_404(book_id)
    
    # Récupérer les sessions de lecture associées à ce livre
    reading_sessions = ReadingSession.query.filter_by(book_id=book_id).order_by(ReadingSession.start_date.desc()).all()
    
    # Récupérer les votes associés à ce livre
    vote_options = VoteOption.query.filter_by(book_id=book_id).all()
    voting_sessions = []
    for option in vote_options:
        if option.voting_session not in voting_sessions:
            voting_sessions.append(option.voting_session)
    
    return render_template('book_detail.html',
                         book=book,
                         reading_sessions=reading_sessions,
                         voting_sessions=voting_sessions)

@main_bp.route('/book/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    book = BookProposal.query.get_or_404(book_id)
      # Vérifier les permissions
    if not current_user.is_admin:
        # Les utilisateurs ne peuvent modifier que leurs propres propositions non approuvées/rejetées
        if book.proposed_by != current_user.id or book.status in ['approved', 'rejected']:
            flash('Vous n\'avez pas l\'autorisation de modifier ce livre.', 'error')
            return redirect(url_for('main.book_detail', book_id=book_id))
    
    form = BookProposalForm(obj=book)
    
    if form.validate_on_submit():
        book.title = form.title.data
        book.author = form.author.data
        book.description = form.description.data
        book.isbn = form.isbn.data
        book.publisher = form.publisher.data
        book.publication_year = form.publication_year.data
        book.pages_count = form.pages_count.data
        book.genre = form.genre.data
        
        db.session.commit()
        
        flash('Les informations du livre ont été mises à jour avec succès!', 'success')
        return redirect(url_for('main.book_detail', book_id=book_id))
    
    return render_template('edit_book.html', form=form, book=book)

@main_bp.route('/book/<int:book_id>/review', methods=['GET', 'POST'])
@login_required
def add_review(book_id):
    book = BookProposal.query.get_or_404(book_id)
    
    # Check if book can be reviewed (completed or archived)
    if not book.can_be_reviewed():
        flash('Ce livre ne peut pas encore être noté car il n\'est pas terminé.', 'warning')
        return redirect(url_for('main.book_detail', book_id=book_id))
    
    # Check if user already has a review for this book
    existing_review = BookReview.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    
    form = BookReviewForm()
    if existing_review and request.method == 'GET':
        form.rating.data = existing_review.rating
        form.comment.data = existing_review.comment
    
    if form.validate_on_submit():
        if existing_review:
            # Update existing review            existing_review.rating = form.rating.data
            existing_review.comment = form.comment.data
            existing_review.updated_at = datetime.now()
            flash('Votre avis a été mis à jour avec succès!', 'success')
        else:
            # Create new review
            review = BookReview(
                user_id=current_user.id,
                book_id=book_id,
                rating=form.rating.data,
                comment=form.comment.data
            )
            db.session.add(review)
            flash('Votre avis a été ajouté avec succès!', 'success')
        
        db.session.commit()
        
        # Vérifier et attribuer des badges pour les avis
        awarded_badges = BadgeManager.check_and_award_badges(current_user.id)
        if awarded_badges:
            badge_names = [badge.name for badge in awarded_badges]
            flash(f'🏆 Félicitations ! Vous avez gagné le(s) badge(s) : {", ".join(badge_names)}', 'success')
        
        return redirect(url_for('main.book_detail', book_id=book_id))
    
    return render_template('add_review.html', form=form, book=book, existing_review=existing_review)

# Nouvelles routes pour les inscriptions aux lectures
@main_bp.route('/reading/<int:reading_id>/register')
@login_required
def register_for_reading(reading_id):
    reading_session = ReadingSession.query.get_or_404(reading_id)
    
    # Vérifier si l'utilisateur n'est pas déjà inscrit
    existing_participation = ReadingParticipation.query.filter_by(
        user_id=current_user.id,
        reading_session_id=reading_id
    ).first()
    
    if existing_participation:
        flash('Vous êtes déjà inscrit à cette lecture.', 'info')
    else:        # Créer une nouvelle participation
        participation = ReadingParticipation(
            user_id=current_user.id,
            reading_session_id=reading_id
        )
        db.session.add(participation)
        db.session.commit()
        
        # Vérifier et attribuer des badges pour les lectures
        awarded_badges = BadgeManager.check_and_award_badges(current_user.id)
        if awarded_badges:
            badge_names = [badge.name for badge in awarded_badges]
            flash(f'🏆 Félicitations ! Vous avez gagné le(s) badge(s) : {", ".join(badge_names)}', 'success')
        
        flash(f'Vous êtes maintenant inscrit à la lecture de "{reading_session.book.title}".', 'success')
    
    return redirect(url_for('main.reading_detail', reading_id=reading_id))

@main_bp.route('/reading/<int:reading_id>/unregister')
@login_required
def unregister_from_reading(reading_id):
    reading_session = ReadingSession.query.get_or_404(reading_id)
    
    # Trouver la participation existante
    participation = ReadingParticipation.query.filter_by(
        user_id=current_user.id,
        reading_session_id=reading_id
    ).first()
    
    if participation:
        db.session.delete(participation)
        db.session.commit()
        flash(f'Vous avez été désinscrit de la lecture de "{reading_session.book.title}".', 'success')
    else:
        flash('Vous n\'étiez pas inscrit à cette lecture.', 'info')
    
    return redirect(url_for('main.reading_detail', reading_id=reading_id))

@main_bp.route('/reading/<int:reading_id>')
def reading_detail(reading_id):
    reading_session = ReadingSession.query.get_or_404(reading_id)
    
    # Récupérer tous les participants avec leurs informations utilisateur
    participants = db.session.query(ReadingParticipation, User).join(
        User, ReadingParticipation.user_id == User.id
    ).filter(
        ReadingParticipation.reading_session_id == reading_id
    ).order_by(ReadingParticipation.joined_at.asc()).all()
    
    # Vérifier si l'utilisateur actuel est inscrit
    user_is_registered = False
    if current_user.is_authenticated:
        user_is_registered = reading_session.is_user_registered(current_user.id)
    
    return render_template('reading_detail.html', 
                         reading=reading_session,
                         participants=participants,
                         user_is_registered=user_is_registered)

@main_bp.route('/user/<int:user_id>')
def user_profile(user_id):
    """Afficher le profil d'un utilisateur avec ses badges et statistiques"""
    user = User.query.get_or_404(user_id)
    
    # Récupérer les badges groupés par catégorie
    badges_by_category = user.get_badges_by_category()
    
    # Récupérer les participations aux lectures
    reading_participations = user.get_reading_participations()
    
    # Récupérer les propositions acceptées
    accepted_proposals = user.get_accepted_proposals()
    
    # Récupérer les statistiques
    stats = user.get_stats()
    
    # Récupérer les avis récents
    recent_reviews = BookReview.query.filter_by(user_id=user.id).order_by(
        BookReview.created_at.desc()
    ).limit(5).all()
    
    return render_template('user_profile.html',
                         user=user,
                         badges_by_category=badges_by_category,
                         reading_participations=reading_participations,
                         accepted_proposals=accepted_proposals,
                         stats=stats,
                         recent_reviews=recent_reviews)

@main_bp.route('/profile')
@login_required
def my_profile():
    """Rediriger vers le profil de l'utilisateur connecté"""
    return redirect(url_for('main.user_profile', user_id=current_user.id))


@main_bp.route('/stats')
def statistics():
    """Page des statistiques publiques"""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Stats générales
    stats = {
        'users': {
            'total': User.query.count(),
            'active': User.query.filter(User.created_at >= datetime.utcnow() - timedelta(days=30)).count()
        },
        'books': {
            'total': BookProposal.query.count(),
            'approved': BookProposal.query.filter_by(status='approved').count(),
            'pending': BookProposal.query.filter_by(status='pending').count(),
            'completed': BookProposal.query.filter_by(status='completed').count()
        },
        'readings': {
            'total': ReadingSession.query.count(),
            'in_progress': ReadingSession.query.filter_by(status='current').count(),
            'completed': ReadingSession.query.filter_by(status='completed').count()
        },
        'badges': {
            'total': Badge.query.count(),
            'awarded': UserBadge.query.count()
        }
    }
    
    # Stats des livres pour le graphique
    book_stats = {
        'approved': stats['books']['approved'],
        'pending': stats['books']['pending'],
        'reading': ReadingSession.query.filter_by(status='current').count(),
        'completed': stats['books']['completed']
    }
    
    # Activité mensuelle (6 derniers mois)
    months = []
    proposals_data = []
    participations_data = []
    
    for i in range(5, -1, -1):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=i*30)
        month_end = month_start + timedelta(days=30)
        
        month_name = month_start.strftime('%b')
        months.append(month_name)
        
        proposals_count = BookProposal.query.filter(
            BookProposal.created_at >= month_start,
            BookProposal.created_at < month_end
        ).count()
        proposals_data.append(proposals_count)
        
        participations_count = ReadingParticipation.query.filter(
            ReadingParticipation.joined_at >= month_start,
            ReadingParticipation.joined_at < month_end
        ).count()
        participations_data.append(participations_count)
    
    activity_data = {
        'labels': months,
        'proposals': proposals_data,
        'participations': participations_data
    }
    
    # Top contributeurs
    top_contributors = db.session.query(
        User,
        (func.count(BookProposal.id) * 10 + 
         func.count(Vote.id) * 2 +
         func.count(ReadingParticipation.id) * 5).label('contribution_score')
    ).outerjoin(
        BookProposal, User.id == BookProposal.proposed_by
    ).outerjoin(
        Vote, User.id == Vote.user_id
    ).outerjoin(
        ReadingParticipation, User.id == ReadingParticipation.user_id
    ).group_by(User.id).order_by(
        db.desc('contribution_score')
    ).limit(10).all()
    
    # Ajouter le score au user pour le template
    top_contributors_with_scores = []
    for user, score in top_contributors:
        user.contribution_score = score
        top_contributors_with_scores.append(user)
    
    # Genres populaires
    genre_stats = db.session.query(
        BookProposal.genre,
        func.count(BookProposal.id).label('count')
    ).filter(
        BookProposal.genre != None,
        BookProposal.genre != ''
    ).group_by(BookProposal.genre).order_by(
        db.desc('count')
    ).limit(6).all()
    
    max_genre_count = genre_stats[0][1] if genre_stats else 1
    popular_genres = [
        {
            'name': genre or 'Non classé',
            'count': count,
            'percentage': int((count / max_genre_count) * 100)
        }
        for genre, count in genre_stats
    ]
    
    # Badges les plus rares
    total_users = User.query.count() or 1
    badge_stats = db.session.query(
        Badge,
        func.count(UserBadge.id).label('owners_count')
    ).outerjoin(
        UserBadge, Badge.id == UserBadge.badge_id
    ).group_by(Badge.id).order_by(
        'owners_count'
    ).limit(6).all()
    
    rare_badges = [
        {
            'name': badge.name,
            'icon': badge.icon,
            'color': badge.color or '#FFD700',
            'owners_count': count,
            'rarity': round((count / total_users) * 100, 1)
        }
        for badge, count in badge_stats
    ]
    
    return render_template('stats.html',
                         stats=stats,
                         book_stats=book_stats,
                         activity_data=activity_data,
                         top_contributors=top_contributors_with_scores,
                         popular_genres=popular_genres,
                         rare_badges=rare_badges)
