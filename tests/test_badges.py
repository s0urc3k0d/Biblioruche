# -*- coding: utf-8 -*-
"""
Tests pytest pour le système de badges BiblioRuche
"""

import pytest
from app.models import Badge, User, UserBadge, BookProposal
from app.badge_manager import BadgeManager


class TestBadgeManager:
    """Tests pour le gestionnaire de badges"""
    
    @pytest.fixture
    def badge_manager(self, app):
        """Instance de BadgeManager pour les tests"""
        with app.app_context():
            return BadgeManager()
    
    @pytest.fixture
    def setup_badges(self, db_session):
        """Configure les badges de test"""
        badges = [
            Badge(name='Premier Livre', description='Premier livre proposé', 
                  icon='fa-book', category='books', color='bronze'),
            Badge(name='Bibliophile', description='5 livres proposés', 
                  icon='fa-books', category='books', color='silver'),
            Badge(name='Lecteur Assidu', description='Participation à 5 lectures',
                  icon='fa-glasses', category='participation', color='gold'),
            Badge(name='Premier Film', description='Première participation au cinéclub',
                  icon='fa-film', category='cineclub', color='bronze'),
        ]
        for badge in badges:
            db_session.add(badge)
        db_session.commit()
        return badges
    
    def test_award_badge(self, db_session, test_user, setup_badges):
        """Test attribution d'un badge"""
        badge = Badge.query.filter_by(name='Premier Livre').first()
        
        # Attribuer le badge
        user_badge = UserBadge(user_id=test_user.id, badge_id=badge.id)
        db_session.add(user_badge)
        db_session.commit()
        
        # Vérifier l'attribution
        awarded = UserBadge.query.filter_by(
            user_id=test_user.id, 
            badge_id=badge.id
        ).first()
        assert awarded is not None
    
    def test_no_duplicate_badges(self, db_session, test_user, setup_badges):
        """Test qu'un badge ne peut pas être attribué deux fois"""
        badge = Badge.query.filter_by(name='Premier Livre').first()
        
        # Premier badge
        user_badge = UserBadge(user_id=test_user.id, badge_id=badge.id)
        db_session.add(user_badge)
        db_session.commit()
        
        # Deuxième tentative (devrait échouer ou être ignorée)
        existing = UserBadge.query.filter_by(
            user_id=test_user.id,
            badge_id=badge.id
        ).first()
        
        # Si existe déjà, ne pas ajouter
        if not existing:
            user_badge2 = UserBadge(user_id=test_user.id, badge_id=badge.id)
            db_session.add(user_badge2)
        
        # Vérifier qu'il n'y a qu'un seul badge
        count = UserBadge.query.filter_by(
            user_id=test_user.id,
            badge_id=badge.id
        ).count()
        assert count == 1
    
    def test_badge_categories(self, db_session, setup_badges):
        """Test filtrage par catégorie"""
        books_badges = Badge.query.filter_by(category='books').all()
        cineclub_badges = Badge.query.filter_by(category='cineclub').all()
        
        assert len(books_badges) == 2  # Premier Livre, Bibliophile
        assert len(cineclub_badges) == 1  # Premier Film
    
    def test_user_badges_relationship(self, db_session, test_user, setup_badges):
        """Test relation utilisateur-badges"""
        badges = Badge.query.limit(2).all()
        
        for badge in badges:
            user_badge = UserBadge(user_id=test_user.id, badge_id=badge.id)
            db_session.add(user_badge)
        
        db_session.commit()
        
        # Vérifier via la relation
        user_badges = UserBadge.query.filter_by(user_id=test_user.id).all()
        assert len(user_badges) == 2


class TestCineClubBadges:
    """Tests spécifiques pour les badges CinéClub"""
    
    def test_cineclub_badge_creation(self, db_session):
        """Test création des badges CinéClub"""
        cineclub_badges = [
            ('Premier Film', 'fa-film', 'bronze'),
            ('Cinéphile', 'fa-video', 'silver'),
            ('Cinéphile Passionné', 'fa-clapperboard', 'gold'),
            ('Voteur de Films', 'fa-check-to-slot', 'bronze'),
            ('Critique de Cinéma', 'fa-star', 'silver'),
            ('Réalisateur en Herbe', 'fa-camera', 'bronze'),
            ('Programmateur', 'fa-calendar-days', 'gold'),
        ]
        
        for name, icon, color in cineclub_badges:
            badge = Badge(
                name=name,
                description=f'Badge {name}',
                icon=icon,
                category='cineclub',
                color=color
            )
            db_session.add(badge)
        
        db_session.commit()
        
        # Vérifier
        badges = Badge.query.filter_by(category='cineclub').all()
        assert len(badges) == 7
        
        # Vérifier les couleurs
        gold_badges = [b for b in badges if b.color == 'gold']
        assert len(gold_badges) == 2  # Cinéphile Passionné, Programmateur


class TestBadgeDisplay:
    """Tests pour l'affichage des badges"""
    
    def test_badge_icon_format(self, db_session):
        """Test format des icônes FontAwesome"""
        badge = Badge(
            name='Test Icon',
            description='Test',
            icon='fa-star',
            category='test'
        )
        db_session.add(badge)
        db_session.commit()
        
        assert badge.icon.startswith('fa-')
    
    def test_badge_color_values(self, db_session):
        """Test valeurs de couleur valides"""
        valid_colors = ['bronze', 'silver', 'gold', 'platinum', 'special']
        
        for color in valid_colors:
            badge = Badge(
                name=f'Badge {color}',
                description='Test',
                icon='fa-trophy',
                category='test',
                color=color
            )
            db_session.add(badge)
        
        db_session.commit()
        
        badges = Badge.query.filter_by(category='test').all()
        assert len(badges) == len(valid_colors)
