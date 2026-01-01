# -*- coding: utf-8 -*-
"""
Tests pour les modèles BiblioRuche
"""

import pytest
from datetime import datetime
from app.models import User, BookProposal, Badge, Reading


class TestUserModel:
    """Tests pour le modèle User"""
    
    def test_create_user(self, db_session):
        """Test création d'un utilisateur"""
        user = User(
            twitch_id='999999',
            username='newuser',
            display_name='New User',
            email='new@example.com'
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'newuser'
        assert user.is_admin == False
        assert user.created_at is not None
    
    def test_user_twitch_id_unique(self, db_session, test_user):
        """Test unicité du twitch_id"""
        duplicate_user = User(
            twitch_id=test_user.twitch_id,  # Même twitch_id
            username='duplicate',
            display_name='Duplicate'
        )
        db_session.add(duplicate_user)
        
        with pytest.raises(Exception):
            db_session.commit()
    
    def test_user_default_values(self, db_session):
        """Test valeurs par défaut"""
        user = User(
            twitch_id='111111',
            username='defaultuser',
            display_name='Default User'
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.is_admin == False
        assert user.avatar_url is None or user.avatar_url == ''


class TestBookProposalModel:
    """Tests pour le modèle BookProposal"""
    
    def test_create_book(self, db_session, test_user):
        """Test création d'un livre"""
        book = BookProposal(
            title='New Book',
            author='Author Name',
            description='Description',
            proposed_by=test_user.id
        )
        db_session.add(book)
        db_session.commit()
        
        assert book.id is not None
        assert book.status == 'pending'
        assert book.proposed_by == test_user.id
    
    def test_book_proposer_relationship(self, db_session, test_user):
        """Test relation avec l'utilisateur proposant"""
        book = BookProposal(
            title='Related Book',
            author='Related Author',
            proposed_by=test_user.id
        )
        db_session.add(book)
        db_session.commit()
        
        assert book.proposer.id == test_user.id
        assert book.proposer.username == test_user.username
    
    def test_book_statuses(self, db_session, test_user):
        """Test différents statuts de livre"""
        for status in ['pending', 'approved', 'rejected', 'reading', 'completed']:
            book = BookProposal(
                title=f'Book {status}',
                author='Author',
                proposed_by=test_user.id,
                status=status
            )
            db_session.add(book)
        
        db_session.commit()
        
        books = BookProposal.query.all()
        statuses = [b.status for b in books]
        assert 'pending' in statuses
        assert 'approved' in statuses


class TestBadgeModel:
    """Tests pour le modèle Badge"""
    
    def test_create_badge(self, db_session):
        """Test création d'un badge"""
        badge = Badge(
            name='Test Badge',
            description='A test badge',
            icon='fa-star',
            category='test',
            color='gold'
        )
        db_session.add(badge)
        db_session.commit()
        
        assert badge.id is not None
        assert badge.name == 'Test Badge'
    
    def test_badge_categories(self, db_session):
        """Test différentes catégories de badges"""
        categories = ['books', 'participation', 'cineclub', 'special']
        
        for cat in categories:
            badge = Badge(
                name=f'Badge {cat}',
                description=f'Badge for {cat}',
                icon='fa-trophy',
                category=cat
            )
            db_session.add(badge)
        
        db_session.commit()
        
        cineclub_badges = Badge.query.filter_by(category='cineclub').all()
        assert len(cineclub_badges) == 1


class TestReadingModel:
    """Tests pour le modèle Reading"""
    
    def test_create_reading(self, db_session, test_book):
        """Test création d'une lecture"""
        reading = Reading(
            book_id=test_book.id,
            status='planned',
            start_date=datetime.utcnow()
        )
        db_session.add(reading)
        db_session.commit()
        
        assert reading.id is not None
        assert reading.book_id == test_book.id
        assert reading.status == 'planned'
    
    def test_reading_statuses(self, db_session, test_book):
        """Test différents statuts de lecture"""
        statuses = ['planned', 'in_progress', 'completed']
        
        for i, status in enumerate(statuses):
            # Créer un nouveau livre pour chaque lecture
            book = BookProposal(
                title=f'Book for {status}',
                author='Author',
                proposed_by=test_book.proposed_by,
                status='approved'
            )
            db_session.add(book)
            db_session.commit()
            
            reading = Reading(
                book_id=book.id,
                status=status
            )
            db_session.add(reading)
        
        db_session.commit()
        
        readings = Reading.query.all()
        assert len(readings) >= 3
