from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
from app import db

def utc_now():
    """Retourne la date/heure actuelle en UTC"""
    return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    twitch_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    display_name = db.Column(db.String(80), nullable=False)    
    email = db.Column(db.String(120))
    avatar_url = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relations
    book_proposals = db.relationship('BookProposal', backref='proposer', lazy=True)
    votes = db.relationship('Vote', backref='voter', lazy=True)
    # Note: created_reading_sessions est déjà défini via le backref 'created_sessions' dans ReadingSession
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def get_badges_by_category(self):
        """Récupérer les badges de l'utilisateur groupés par catégorie"""
        badges_dict = {}
        for user_badge in self.user_badges:
            category = user_badge.badge.category
            if category not in badges_dict:
                badges_dict[category] = []
            badges_dict[category].append(user_badge)
        return badges_dict
    
    def has_badge(self, badge_name):
        """Vérifier si l'utilisateur possède un badge spécifique"""
        return any(ub.badge.name == badge_name for ub in self.user_badges)
    
    def get_reading_participations(self):
        """Récupérer les lectures auxquelles l'utilisateur a participé"""
        return ReadingParticipation.query.filter_by(user_id=self.id).order_by(ReadingParticipation.joined_at.desc()).all()
    
    def get_accepted_proposals(self):
        """Récupérer les propositions de livres acceptées de l'utilisateur"""
        return BookProposal.query.filter_by(
            proposed_by=self.id,
            status='approved'
        ).order_by(BookProposal.created_at.desc()).all()
    
    def get_stats(self):
        """Récupérer les statistiques de l'utilisateur pour les badges"""
        return {
            'total_proposals': len(self.book_proposals),
            'accepted_proposals': len(self.get_accepted_proposals()),
            'total_votes': len(self.votes),
            'total_participations': len(self.get_reading_participations()),
            'total_reviews': BookReview.query.filter_by(user_id=self.id).count(),
            'average_rating': db.session.query(db.func.avg(BookReview.rating)).filter_by(user_id=self.id).scalar() or 0
        }

class BookProposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    isbn = db.Column(db.String(20))
    publisher = db.Column(db.String(100))
    publication_year = db.Column(db.Integer)
    pages_count = db.Column(db.Integer)
    genre = db.Column(db.String(100))
    proposed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, in_vote, selected, archived
    created_at = db.Column(db.DateTime, default=utc_now)
    
    def get_average_rating(self):
        """Calculate average rating from all reviews"""
        if not self.reviews:
            return 0
        visible_reviews = [r for r in self.reviews if r.is_visible]
        if not visible_reviews:
            return 0
        return round(sum(r.rating for r in visible_reviews) / len(visible_reviews), 1)
    
    def get_review_count(self):
        """Get count of visible reviews"""
        return len([r for r in self.reviews if r.is_visible])
    
    def can_be_reviewed(self):
        """Check if book can be reviewed (completed or archived)"""
        # Check if book has reading sessions that are completed or archived
        for session in self.reading_sessions:
            if session.status in ['completed', 'archived']:
                return True
        return False
    
    def __repr__(self):
        return f'<BookProposal {self.title} by {self.author}>'

class ReadingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book_proposal.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    debrief_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='upcoming', nullable=False)  # upcoming, current, completed, archived
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relations
    book = db.relationship('BookProposal', backref='reading_sessions')
    creator = db.relationship('User', backref='created_sessions')
    
    def get_participants_count(self):
        """Get count of users registered for this reading session"""
        return len(self.participants)
    
    def is_user_registered(self, user_id):
        """Check if a user is registered for this reading session"""
        return any(p.user_id == user_id for p in self.participants)
    
    def __repr__(self):
        return f'<ReadingSession {self.book.title}>'

class ReadingParticipation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reading_session_id = db.Column(db.Integer, db.ForeignKey('reading_session.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=utc_now)
    
    # Relations
    user = db.relationship('User', backref='reading_participations')
    reading_session = db.relationship('ReadingSession', backref='participants')
    
    # Unique constraint to ensure one participation per user per reading session
    __table_args__ = (db.UniqueConstraint('user_id', 'reading_session_id', name='unique_user_reading_participation'),)
    
    def __repr__(self):
        return f'<ReadingParticipation {self.user.username} in {self.reading_session.book.title}>'

class VotingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, default=utc_now)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)  # active, closed
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    winner_book_id = db.Column(db.Integer, db.ForeignKey('book_proposal.id'))
    
    # Relations
    creator = db.relationship('User', backref='created_votes')
    winner_book = db.relationship('BookProposal')
    books = db.relationship('VoteOption', backref='voting_session', lazy=True)
    votes = db.relationship('Vote', backref='voting_session', lazy=True)
    
    def __repr__(self):
        return f'<VotingSession {self.title}>'

class VoteOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voting_session_id = db.Column(db.Integer, db.ForeignKey('voting_session.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book_proposal.id'), nullable=False)
    
    # Relations
    book = db.relationship('BookProposal')
    
    def get_vote_count(self):
        return Vote.query.filter_by(vote_option_id=self.id).count()

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    voting_session_id = db.Column(db.Integer, db.ForeignKey('voting_session.id'), nullable=False)
    vote_option_id = db.Column(db.Integer, db.ForeignKey('vote_option.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relations
    vote_option = db.relationship('VoteOption')

class BookReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book_proposal.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5 stars
    comment = db.Column(db.Text)
    is_moderated = db.Column(db.Boolean, default=False, nullable=False)  # For admin moderation
    is_visible = db.Column(db.Boolean, default=True, nullable=False)  # Can be hidden by admin
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Relations
    user = db.relationship('User', backref='reviews')
    book = db.relationship('BookProposal', backref='reviews')
    
    # Unique constraint to ensure one review per user per book
    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_user_book_review'),)
    
    def __repr__(self):
        return f'<BookReview {self.book.title} by {self.user.username}: {self.rating}/5>'

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), nullable=False)  # FontAwesome icon class
    category = db.Column(db.String(50), nullable=False)  # lecture, notation, vote, proposition
    color = db.Column(db.String(20), default='primary')  # Bootstrap color class
    
    def __repr__(self):
        return f'<Badge {self.name}>'

class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=utc_now)
    
    # Relations
    user = db.relationship('User', backref='user_badges')
    badge = db.relationship('Badge', backref='badge_users')
    
    # Unique constraint to prevent duplicate badges
    __table_args__ = (db.UniqueConstraint('user_id', 'badge_id', name='unique_user_badge'),)
    
    def __repr__(self):
        return f'<UserBadge {self.user.username} - {self.badge.name}>'


# =============================================================================
# MODÈLES BIBLIOTHÈQUE EBOOKS
# =============================================================================

class Ebook(db.Model):
    """Modèle pour les ebooks de la bibliothèque"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    isbn = db.Column(db.String(20))
    genre = db.Column(db.String(100))
    publication_year = db.Column(db.Integer)
    pages_count = db.Column(db.Integer)
    
    # Fichier EPUB
    filename = db.Column(db.String(255), nullable=False)  # Nom du fichier stocké
    original_filename = db.Column(db.String(255), nullable=False)  # Nom original
    file_size = db.Column(db.Integer)  # Taille en bytes
    
    # Image de couverture (optionnelle)
    cover_filename = db.Column(db.String(255))
    
    # Métadonnées
    download_count = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Lien optionnel vers une proposition de livre existante
    book_proposal_id = db.Column(db.Integer, db.ForeignKey('book_proposal.id'))
    
    # Relations
    uploader = db.relationship('User', backref='uploaded_ebooks')
    book_proposal = db.relationship('BookProposal', backref='ebook')
    
    def get_file_size_display(self):
        """Affiche la taille du fichier de manière lisible"""
        if not self.file_size:
            return "Inconnu"
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def __repr__(self):
        return f'<Ebook {self.title} by {self.author}>'


# =============================================================================
# MODÈLES BIBLIOCINECLUB
# =============================================================================

class CineClubSettings(db.Model):
    """Configuration globale du module CinéClub"""
    id = db.Column(db.Integer, primary_key=True)
    is_enabled = db.Column(db.Boolean, default=False, nullable=False)
    module_name = db.Column(db.String(100), default='BiblioCinéClub')
    description = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Relations
    updater = db.relationship('User', backref='cineclub_settings_updates')
    
    @staticmethod
    def get_settings():
        """Récupère ou crée les paramètres du CinéClub"""
        settings = CineClubSettings.query.first()
        if not settings:
            settings = CineClubSettings(is_enabled=False)
            db.session.add(settings)
            db.session.commit()
        return settings


class Film(db.Model):
    """Modèle pour les films proposés/votés"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    original_title = db.Column(db.String(200))  # Titre original si étranger
    director = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer)
    genre = db.Column(db.String(100))
    duration = db.Column(db.Integer)  # Durée en minutes
    synopsis = db.Column(db.Text)
    poster_url = db.Column(db.String(500))  # URL de l'affiche
    imdb_url = db.Column(db.String(500))
    trailer_url = db.Column(db.String(500))  # URL YouTube/autre
    
    # Métadonnées
    proposed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, selected, viewed, archived
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relations
    proposer = db.relationship('User', backref='proposed_films')
    
    def get_duration_display(self):
        """Affiche la durée en format heures:minutes"""
        if not self.duration:
            return "Durée inconnue"
        hours = self.duration // 60
        minutes = self.duration % 60
        if hours > 0:
            return f"{hours}h{minutes:02d}"
        return f"{minutes} min"
    
    def __repr__(self):
        return f'<Film {self.title} ({self.year})>'


class FilmVotingSession(db.Model):
    """Session de vote pour choisir un film"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, default=utc_now)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)  # active, closed
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    winner_film_id = db.Column(db.Integer, db.ForeignKey('film.id'))
    
    # Relations
    creator = db.relationship('User', backref='created_film_votes')
    winner_film = db.relationship('Film', foreign_keys=[winner_film_id])
    options = db.relationship('FilmVoteOption', backref='voting_session', lazy=True)
    votes = db.relationship('FilmVote', backref='voting_session', lazy=True)
    
    def __repr__(self):
        return f'<FilmVotingSession {self.title}>'


class FilmVoteOption(db.Model):
    """Options de vote (films candidats) dans une session"""
    id = db.Column(db.Integer, primary_key=True)
    voting_session_id = db.Column(db.Integer, db.ForeignKey('film_voting_session.id'), nullable=False)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'), nullable=False)
    
    # Relations
    film = db.relationship('Film')
    
    def get_vote_count(self):
        return FilmVote.query.filter_by(vote_option_id=self.id).count()


class FilmVote(db.Model):
    """Vote d'un utilisateur pour un film"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    voting_session_id = db.Column(db.Integer, db.ForeignKey('film_voting_session.id'), nullable=False)
    vote_option_id = db.Column(db.Integer, db.ForeignKey('film_vote_option.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relations
    voter = db.relationship('User', backref='film_votes')
    vote_option = db.relationship('FilmVoteOption')
    
    # Unique constraint - un vote par utilisateur par session
    __table_args__ = (db.UniqueConstraint('user_id', 'voting_session_id', name='unique_user_film_vote'),)


class ViewingSession(db.Model):
    """Session de visionnage planifiée"""
    id = db.Column(db.Integer, primary_key=True)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'), nullable=False)
    scheduled_date = db.Column(db.DateTime, nullable=False)
    stream_url = db.Column(db.String(500))  # URL du stream Twitch/Discord
    status = db.Column(db.String(20), default='upcoming', nullable=False)  # upcoming, live, completed, cancelled
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relations
    film = db.relationship('Film', backref='viewing_sessions')
    creator = db.relationship('User', backref='created_viewing_sessions')
    
    def get_participants_count(self):
        return len(self.participants)
    
    def is_user_registered(self, user_id):
        return any(p.user_id == user_id for p in self.participants)
    
    def __repr__(self):
        return f'<ViewingSession {self.film.title}>'


class ViewingParticipation(db.Model):
    """Participation d'un utilisateur à une séance de visionnage"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    viewing_session_id = db.Column(db.Integer, db.ForeignKey('viewing_session.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=utc_now)
    
    # Relations
    user = db.relationship('User', backref='viewing_participations')
    viewing_session = db.relationship('ViewingSession', backref='participants')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'viewing_session_id', name='unique_user_viewing_participation'),)


class Notification(db.Model):
    """Notification in-app pour les utilisateurs"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # badge, vote, reading, review, system
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(500))  # URL optionnel vers le contenu lié
    icon = db.Column(db.String(50))  # Icône FontAwesome
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    read_at = db.Column(db.DateTime)
    
    # Relations
    user = db.relationship('User', backref='notifications')
    
    @classmethod
    def create_notification(cls, user_id, notification_type, title, message, link=None, icon=None):
        """Crée et enregistre une nouvelle notification"""
        from app import db
        notification = cls(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            link=link,
            icon=icon or cls.get_default_icon(notification_type)
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @staticmethod
    def get_default_icon(notification_type):
        """Retourne l'icône par défaut selon le type"""
        icons = {
            'badge': 'fa-medal',
            'vote': 'fa-check-to-slot',
            'reading': 'fa-book-open',
            'review': 'fa-star',
            'cineclub': 'fa-film',
            'system': 'fa-bell'
        }
        return icons.get(notification_type, 'fa-bell')
    
    def mark_as_read(self):
        """Marque la notification comme lue"""
        self.is_read = True
        self.read_at = utc_now()
    
    @classmethod
    def get_unread_count(cls, user_id):
        """Retourne le nombre de notifications non lues"""
        return cls.query.filter_by(user_id=user_id, is_read=False).count()
    
    @classmethod
    def get_recent(cls, user_id, limit=20):
        """Retourne les notifications récentes"""
        return cls.query.filter_by(user_id=user_id).order_by(
            cls.is_read.asc(),
            cls.created_at.desc()
        ).limit(limit).all()
    
    def __repr__(self):
        return f'<Notification {self.type}: {self.title}>'

