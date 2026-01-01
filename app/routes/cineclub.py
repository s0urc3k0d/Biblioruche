# -*- coding: utf-8 -*-
"""
Routes pour le module CinéBookClub
Module activable/désactivable pour les combos Livre+Film (adaptations)
"""

from functools import wraps
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db, limiter
from app.models import (
    CineClubSettings, Film, FilmVotingSession, FilmVoteOption, 
    FilmVote, ViewingSession, ViewingParticipation, BookProposal
)

cineclub_bp = Blueprint('cineclub', __name__, url_prefix='/cineclub')


def utc_now():
    """Retourne la date/heure actuelle en UTC"""
    return datetime.now(timezone.utc)


def cineclub_enabled(f):
    """Décorateur pour vérifier que le CinéClub est activé"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        settings = CineClubSettings.get_settings()
        if not settings.is_enabled:
            flash('Le BiblioCinéClub est actuellement désactivé.', 'info')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Décorateur pour les routes admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Accès réservé aux administrateurs.', 'danger')
            return redirect(url_for('cineclub.index'))
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# ROUTES PUBLIQUES
# =============================================================================

@cineclub_bp.route('/')
@cineclub_enabled
def index():
    """Page d'accueil du CinéClub"""
    settings = CineClubSettings.get_settings()
    
    # Votes actifs
    active_votes = FilmVotingSession.query.filter_by(status='active').order_by(
        FilmVotingSession.end_date
    ).all()
    
    # Séances de visionnage à venir
    upcoming_viewings = ViewingSession.query.filter(
        ViewingSession.status.in_(['upcoming', 'live'])
    ).order_by(ViewingSession.scheduled_date).limit(5).all()
    
    # Films récemment ajoutés
    recent_films = Film.query.filter_by(status='approved').order_by(
        Film.created_at.desc()
    ).limit(6).all()
    
    return render_template('cineclub/index.html',
                          settings=settings,
                          active_votes=active_votes,
                          upcoming_viewings=upcoming_viewings,
                          recent_films=recent_films)


@cineclub_bp.route('/films')
@cineclub_enabled
def list_films():
    """Liste des films proposés"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    status_filter = request.args.get('status', '')
    genre = request.args.get('genre', '')
    search = request.args.get('search', '')
    
    query = Film.query
    
    # Filtrer par statut (seulement les films visibles pour les non-admin)
    if status_filter:
        query = query.filter(Film.status == status_filter)
    elif not current_user.is_authenticated or not current_user.is_admin:
        query = query.filter(Film.status.in_(['approved', 'selected', 'viewed']))
    
    if genre:
        query = query.filter(Film.genre == genre)
    
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Film.title.ilike(search_term),
                Film.director.ilike(search_term)
            )
        )
    
    films = query.order_by(Film.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Genres uniques pour le filtre
    genres = db.session.query(Film.genre).filter(
        Film.genre.isnot(None)
    ).distinct().order_by(Film.genre).all()
    genres = [g[0] for g in genres if g[0]]
    
    return render_template('cineclub/films.html',
                          films=films,
                          genres=genres,
                          current_genre=genre,
                          current_status=status_filter,
                          search=search)


@cineclub_bp.route('/film/<int:film_id>')
@cineclub_enabled
def film_detail(film_id):
    """Détails d'un film"""
    film = Film.query.get_or_404(film_id)
    
    # Vérifier visibilité pour non-admin
    if film.status == 'pending' and (not current_user.is_authenticated or not current_user.is_admin):
        abort(404)
    
    return render_template('cineclub/film_detail.html', film=film)


@cineclub_bp.route('/propose', methods=['GET', 'POST'])
@login_required
@admin_required  # Seuls les admins peuvent proposer des films (CinéBookClub)
@cineclub_enabled
def propose_film():
    """Proposer un nouveau film (admin uniquement) - CinéBookClub"""
    # Récupérer les livres disponibles pour liaison
    available_books = BookProposal.query.filter(
        BookProposal.status.in_(['approved', 'reading', 'completed', 'archived'])
    ).order_by(BookProposal.title).all()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        director = request.form.get('director', '').strip()
        book_id = request.form.get('book_proposal_id', type=int)
        
        if not title or not director:
            flash('Le titre et le réalisateur sont obligatoires.', 'danger')
            return redirect(request.url)
        
        if not book_id:
            flash('Vous devez associer le film à un livre (adaptation).', 'danger')
            return redirect(request.url)
        
        # Récupérer les plateformes sélectionnées
        platforms = request.form.getlist('platforms')
        platforms_str = ','.join(platforms) if platforms else ''
        
        film = Film(
            title=title,
            original_title=request.form.get('original_title', '').strip() or None,
            director=director,
            year=request.form.get('year', type=int) or None,
            genre=request.form.get('genre', '').strip() or None,
            duration=request.form.get('duration', type=int) or None,
            synopsis=request.form.get('synopsis', '').strip() or None,
            poster_url=request.form.get('poster_url', '').strip() or None,
            imdb_url=request.form.get('imdb_url', '').strip() or None,
            trailer_url=request.form.get('trailer_url', '').strip() or None,
            book_proposal_id=book_id,
            platforms=platforms_str,
            proposed_by=current_user.id,
            status='approved'  # Directement approuvé car admin
        )
        
        db.session.add(film)
        db.session.commit()
        
        flash(f'Film "{film.title}" ajouté avec succès !', 'success')
        return redirect(url_for('cineclub.film_detail', film_id=film.id))
    
    return render_template('cineclub/propose_film.html', 
                          available_books=available_books,
                          platforms=Film.PLATFORMS)


# =============================================================================
# ROUTES VOTES
# =============================================================================

@cineclub_bp.route('/votes')
@cineclub_enabled
def list_votes():
    """Liste des sessions de vote"""
    active_votes = FilmVotingSession.query.filter_by(status='active').order_by(
        FilmVotingSession.end_date
    ).all()
    
    closed_votes = FilmVotingSession.query.filter_by(status='closed').order_by(
        FilmVotingSession.end_date.desc()
    ).limit(10).all()
    
    return render_template('cineclub/votes.html',
                          active_votes=active_votes,
                          closed_votes=closed_votes)


@cineclub_bp.route('/vote/<int:vote_id>')
@cineclub_enabled
def vote_detail(vote_id):
    """Détails d'une session de vote"""
    vote_session = FilmVotingSession.query.get_or_404(vote_id)
    
    # Vérifier si l'utilisateur a déjà voté
    user_vote = None
    if current_user.is_authenticated:
        user_vote = FilmVote.query.filter_by(
            user_id=current_user.id,
            voting_session_id=vote_id
        ).first()
    
    return render_template('cineclub/vote_detail.html',
                          vote_session=vote_session,
                          user_vote=user_vote)


@cineclub_bp.route('/vote/<int:vote_id>/submit', methods=['POST'])
@login_required
@cineclub_enabled
@limiter.limit("10 per hour")
def submit_vote(vote_id):
    """Soumettre un vote"""
    vote_session = FilmVotingSession.query.get_or_404(vote_id)
    
    if vote_session.status != 'active':
        flash('Cette session de vote est fermée.', 'warning')
        return redirect(url_for('cineclub.vote_detail', vote_id=vote_id))
    
    # Vérifier si déjà voté
    existing_vote = FilmVote.query.filter_by(
        user_id=current_user.id,
        voting_session_id=vote_id
    ).first()
    
    if existing_vote:
        flash('Vous avez déjà voté pour cette session.', 'warning')
        return redirect(url_for('cineclub.vote_detail', vote_id=vote_id))
    
    option_id = request.form.get('vote_option_id', type=int)
    if not option_id:
        flash('Veuillez sélectionner un film.', 'danger')
        return redirect(url_for('cineclub.vote_detail', vote_id=vote_id))
    
    # Vérifier que l'option existe et appartient à cette session
    option = FilmVoteOption.query.filter_by(
        id=option_id,
        voting_session_id=vote_id
    ).first()
    
    if not option:
        flash('Option de vote invalide.', 'danger')
        return redirect(url_for('cineclub.vote_detail', vote_id=vote_id))
    
    # Créer le vote
    vote = FilmVote(
        user_id=current_user.id,
        voting_session_id=vote_id,
        vote_option_id=option_id
    )
    
    db.session.add(vote)
    db.session.commit()
    
    flash('Votre vote a été enregistré !', 'success')
    return redirect(url_for('cineclub.vote_detail', vote_id=vote_id))


# =============================================================================
# ROUTES SÉANCES DE VISIONNAGE
# =============================================================================

@cineclub_bp.route('/viewings')
@cineclub_enabled
def list_viewings():
    """Liste des séances de visionnage"""
    upcoming = ViewingSession.query.filter(
        ViewingSession.status.in_(['upcoming', 'live'])
    ).order_by(ViewingSession.scheduled_date).all()
    
    past = ViewingSession.query.filter_by(status='completed').order_by(
        ViewingSession.scheduled_date.desc()
    ).limit(10).all()
    
    return render_template('cineclub/viewings.html',
                          upcoming=upcoming,
                          past=past)


@cineclub_bp.route('/viewing/<int:viewing_id>')
@cineclub_enabled
def viewing_detail(viewing_id):
    """Détails d'une séance de visionnage"""
    viewing = ViewingSession.query.get_or_404(viewing_id)
    
    is_registered = False
    if current_user.is_authenticated:
        is_registered = viewing.is_user_registered(current_user.id)
    
    return render_template('cineclub/viewing_detail.html',
                          viewing=viewing,
                          is_registered=is_registered)


@cineclub_bp.route('/viewing/<int:viewing_id>/register', methods=['POST'])
@login_required
@cineclub_enabled
def register_viewing(viewing_id):
    """S'inscrire à une séance de visionnage"""
    viewing = ViewingSession.query.get_or_404(viewing_id)
    
    if viewing.status not in ['upcoming', 'live']:
        flash('Cette séance n\'est plus disponible.', 'warning')
        return redirect(url_for('cineclub.viewing_detail', viewing_id=viewing_id))
    
    if viewing.is_user_registered(current_user.id):
        flash('Vous êtes déjà inscrit à cette séance.', 'info')
        return redirect(url_for('cineclub.viewing_detail', viewing_id=viewing_id))
    
    participation = ViewingParticipation(
        user_id=current_user.id,
        viewing_session_id=viewing_id
    )
    
    db.session.add(participation)
    db.session.commit()
    
    flash('Vous êtes inscrit à la séance !', 'success')
    return redirect(url_for('cineclub.viewing_detail', viewing_id=viewing_id))


@cineclub_bp.route('/viewing/<int:viewing_id>/unregister', methods=['POST'])
@login_required
@cineclub_enabled
def unregister_viewing(viewing_id):
    """Se désinscrire d'une séance de visionnage"""
    viewing = ViewingSession.query.get_or_404(viewing_id)
    
    participation = ViewingParticipation.query.filter_by(
        user_id=current_user.id,
        viewing_session_id=viewing_id
    ).first()
    
    if not participation:
        flash('Vous n\'êtes pas inscrit à cette séance.', 'info')
        return redirect(url_for('cineclub.viewing_detail', viewing_id=viewing_id))
    
    db.session.delete(participation)
    db.session.commit()
    
    flash('Vous vous êtes désinscrit de la séance.', 'info')
    return redirect(url_for('cineclub.viewing_detail', viewing_id=viewing_id))


# =============================================================================
# ROUTES ADMIN
# =============================================================================

@cineclub_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Dashboard admin du CinéBookClub"""
    settings = CineClubSettings.get_settings()
    
    # Stats
    stats = {
        'total_films': Film.query.filter(Film.status.in_(['approved', 'selected', 'viewed'])).count(),
        'active_votes': FilmVotingSession.query.filter_by(status='active').count(),
        'upcoming_viewings': ViewingSession.query.filter_by(status='upcoming').count()
    }
    
    return render_template('cineclub/admin/dashboard.html',
                          settings=settings,
                          stats=stats,
                          Film=Film)  # Passer le modèle pour les requêtes dans le template


@cineclub_bp.route('/admin/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_cineclub():
    """Activer/désactiver le module CinéBookClub"""
    settings = CineClubSettings.get_settings()
    settings.is_enabled = not settings.is_enabled
    settings.updated_by = current_user.id
    db.session.commit()
    
    status = "activé" if settings.is_enabled else "désactivé"
    flash(f'CinéBookClub {status} !', 'success')
    return redirect(url_for('cineclub.admin_dashboard'))


@cineclub_bp.route('/admin/film/<int:film_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_film(film_id):
    """Approuver une proposition de film"""
    film = Film.query.get_or_404(film_id)
    film.status = 'approved'
    db.session.commit()
    
    flash(f'Film "{film.title}" approuvé !', 'success')
    return redirect(url_for('cineclub.admin_dashboard'))


@cineclub_bp.route('/admin/film/<int:film_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_film(film_id):
    """Rejeter une proposition de film"""
    film = Film.query.get_or_404(film_id)
    film.status = 'archived'
    db.session.commit()
    
    flash(f'Film "{film.title}" rejeté.', 'info')
    return redirect(url_for('cineclub.admin_dashboard'))


@cineclub_bp.route('/admin/film/<int:film_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_film(film_id):
    """Éditer un film existant"""
    film = Film.query.get_or_404(film_id)
    
    # Récupérer les livres disponibles pour liaison
    available_books = BookProposal.query.filter(
        BookProposal.status.in_(['approved', 'reading', 'completed', 'archived'])
    ).order_by(BookProposal.title).all()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        director = request.form.get('director', '').strip()
        book_id = request.form.get('book_proposal_id', type=int)
        
        if not title or not director:
            flash('Le titre et le réalisateur sont obligatoires.', 'danger')
            return redirect(request.url)
        
        # Récupérer les plateformes sélectionnées
        platforms = request.form.getlist('platforms')
        platforms_str = ','.join(platforms) if platforms else ''
        
        film.title = title
        film.original_title = request.form.get('original_title', '').strip() or None
        film.director = director
        film.year = request.form.get('year', type=int) or None
        film.genre = request.form.get('genre', '').strip() or None
        film.duration = request.form.get('duration', type=int) or None
        film.synopsis = request.form.get('synopsis', '').strip() or None
        film.poster_url = request.form.get('poster_url', '').strip() or None
        film.imdb_url = request.form.get('imdb_url', '').strip() or None
        film.trailer_url = request.form.get('trailer_url', '').strip() or None
        film.book_proposal_id = book_id
        film.platforms = platforms_str
        
        db.session.commit()
        
        flash(f'Film "{film.title}" mis à jour !', 'success')
        return redirect(url_for('cineclub.film_detail', film_id=film.id))
    
    # Pré-sélectionner les plateformes actuelles
    selected_platforms = film.get_platforms_list() if film.platforms else []
    
    return render_template('cineclub/admin/edit_film.html', 
                          film=film,
                          available_books=available_books,
                          platforms=Film.PLATFORMS,
                          selected_platforms=selected_platforms)


@cineclub_bp.route('/admin/film/<int:film_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_film(film_id):
    """Supprimer un film"""
    film = Film.query.get_or_404(film_id)
    title = film.title
    
    db.session.delete(film)
    db.session.commit()
    
    flash(f'Film "{title}" supprimé.', 'info')
    return redirect(url_for('cineclub.list_films'))


@cineclub_bp.route('/admin/vote/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_vote():
    """Créer une session de vote pour films"""
    approved_films = Film.query.filter_by(status='approved').order_by(Film.title).all()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Le titre est obligatoire.', 'danger')
            return redirect(request.url)
        
        end_date_str = request.form.get('end_date')
        try:
            end_date = datetime.fromisoformat(end_date_str)
        except (ValueError, TypeError):
            flash('Date de fin invalide.', 'danger')
            return redirect(request.url)
        
        film_ids = request.form.getlist('film_ids', type=int)
        if len(film_ids) < 2:
            flash('Sélectionnez au moins 2 films.', 'danger')
            return redirect(request.url)
        
        vote_session = FilmVotingSession(
            title=title,
            description=request.form.get('description', '').strip() or None,
            end_date=end_date,
            created_by=current_user.id
        )
        db.session.add(vote_session)
        db.session.flush()  # Pour obtenir l'ID
        
        # Ajouter les options de vote
        for film_id in film_ids:
            option = FilmVoteOption(
                voting_session_id=vote_session.id,
                film_id=film_id
            )
            db.session.add(option)
        
        db.session.commit()
        
        flash(f'Session de vote "{title}" créée !', 'success')
        return redirect(url_for('cineclub.admin_dashboard'))
    
    return render_template('cineclub/admin/create_vote.html', approved_films=approved_films)


@cineclub_bp.route('/admin/vote/<int:vote_id>/close', methods=['POST'])
@login_required
@admin_required
def close_vote(vote_id):
    """Fermer une session de vote et déterminer le gagnant"""
    vote_session = FilmVotingSession.query.get_or_404(vote_id)
    
    if vote_session.status != 'active':
        flash('Cette session est déjà fermée.', 'warning')
        return redirect(url_for('cineclub.admin_dashboard'))
    
    # Trouver le gagnant
    winner_option = None
    max_votes = 0
    
    for option in vote_session.options:
        vote_count = option.get_vote_count()
        if vote_count > max_votes:
            max_votes = vote_count
            winner_option = option
    
    vote_session.status = 'closed'
    if winner_option:
        vote_session.winner_film_id = winner_option.film_id
        winner_option.film.status = 'selected'
    
    db.session.commit()
    
    flash('Session de vote fermée !', 'success')
    return redirect(url_for('cineclub.admin_dashboard'))


@cineclub_bp.route('/admin/viewing/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_viewing():
    """Créer une séance de visionnage"""
    selected_films = Film.query.filter_by(status='selected').order_by(Film.title).all()
    
    if request.method == 'POST':
        film_id = request.form.get('film_id', type=int)
        if not film_id:
            flash('Sélectionnez un film.', 'danger')
            return redirect(request.url)
        
        scheduled_date_str = request.form.get('scheduled_date')
        try:
            scheduled_date = datetime.fromisoformat(scheduled_date_str)
        except (ValueError, TypeError):
            flash('Date invalide.', 'danger')
            return redirect(request.url)
        
        viewing = ViewingSession(
            film_id=film_id,
            scheduled_date=scheduled_date,
            stream_url=request.form.get('stream_url', '').strip() or None,
            description=request.form.get('description', '').strip() or None,
            created_by=current_user.id
        )
        
        db.session.add(viewing)
        db.session.commit()
        
        flash('Séance de visionnage créée !', 'success')
        return redirect(url_for('cineclub.admin_dashboard'))
    
    return render_template('cineclub/admin/create_viewing.html', selected_films=selected_films)


@cineclub_bp.route('/admin/viewing/<int:viewing_id>/start', methods=['POST'])
@login_required
@admin_required
def start_viewing(viewing_id):
    """Marquer une séance comme en direct"""
    viewing = ViewingSession.query.get_or_404(viewing_id)
    viewing.status = 'live'
    db.session.commit()
    
    flash('Séance démarrée !', 'success')
    return redirect(url_for('cineclub.admin_dashboard'))


@cineclub_bp.route('/admin/viewing/<int:viewing_id>/complete', methods=['POST'])
@login_required
@admin_required
def complete_viewing(viewing_id):
    """Marquer une séance comme terminée"""
    viewing = ViewingSession.query.get_or_404(viewing_id)
    viewing.status = 'completed'
    viewing.film.status = 'viewed'
    db.session.commit()
    
    flash('Séance terminée !', 'success')
    return redirect(url_for('cineclub.admin_dashboard'))
