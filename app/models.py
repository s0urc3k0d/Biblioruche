from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    twitch_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    display_name = db.Column(db.String(80), nullable=False)    
    email = db.Column(db.String(120))
    avatar_url = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
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
    created_at = db.Column(db.DateTime, default=datetime.now)
    
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
    created_at = db.Column(db.DateTime, default=datetime.now)
    
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
    joined_at = db.Column(db.DateTime, default=datetime.now)
    
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
    start_date = db.Column(db.DateTime, default=datetime.now)
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
    created_at = db.Column(db.DateTime, default=datetime.now)
    
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
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
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
    earned_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relations
    user = db.relationship('User', backref='user_badges')
    badge = db.relationship('Badge', backref='badge_users')
    
    # Unique constraint to prevent duplicate badges
    __table_args__ = (db.UniqueConstraint('user_id', 'badge_id', name='unique_user_badge'),)
    
    def __repr__(self):
        return f'<UserBadge {self.user.username} - {self.badge.name}>'
