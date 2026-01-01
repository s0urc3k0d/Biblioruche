"""Script simple pour créer des données de test"""
import sys
sys.path.append('.')

from app import create_app, db
from app.models import User, BookProposal, VotingSession, VoteOption, Vote, ReadingSession
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    print("🗃️ Création des données de test...")
    
    # Créer des utilisateurs
    admin = User(
        twitch_id='wenyn_123',
        username='wenyn',
        display_name='Wenyn',
        email='wenyn@test.com',
        is_admin=True
    )
    
    user1 = User(
        twitch_id='reader1_456',
        username='bookworm',
        display_name='BookWorm',
        email='reader@test.com',
        is_admin=False
    )
    
    db.session.add(admin)
    db.session.add(user1)
    db.session.commit()
    
    print(f"✅ Utilisateurs créés: {User.query.count()}")
    
    # Créer des livres
    book1 = BookProposal(
        title="Le Nom du Vent",
        author="Patrick Rothfuss",
        description="Premier tome de la Chronique du Tueur de Roi",
        genre="Fantasy",
        page_count=650,
        difficulty_level="intermediate",
        proposed_by=user1.id,
        status='pending'
    )
    
    book2 = BookProposal(
        title="Dune",
        author="Frank Herbert",
        description="Chef-d'œuvre de la science-fiction",
        genre="Science-Fiction",
        page_count=688,
        difficulty_level="advanced",
        proposed_by=admin.id,
        status='approved'
    )
    
    book3 = BookProposal(
        title="Le Hobbit",
        author="J.R.R. Tolkien",
        description="Les aventures de Bilbon Sacquet",
        genre="Fantasy",
        page_count=310,
        difficulty_level="beginner",
        proposed_by=user1.id,
        status='selected'
    )
    
    db.session.add(book1)
    db.session.add(book2)
    db.session.add(book3)
    db.session.commit()
    
    print(f"✅ Livres créés: {BookProposal.query.count()}")
    
    # Créer un vote actif
    vote = VotingSession(
        title="Choix du livre pour Juin 2025",
        description="Votez pour le prochain livre !",
        start_date=datetime.now() - timedelta(days=1),
        end_date=datetime.now() + timedelta(days=7),
        created_by=admin.id,
        status='active'
    )
    db.session.add(vote)
    db.session.commit()
    
    # Options de vote
    option1 = VoteOption(voting_session_id=vote.id, book_id=book1.id)
    option2 = VoteOption(voting_session_id=vote.id, book_id=book2.id)
    db.session.add(option1)
    db.session.add(option2)
    db.session.commit()
    
    # Votes
    vote1 = Vote(voting_session_id=vote.id, option_id=option1.id, user_id=user1.id)
    vote2 = Vote(voting_session_id=vote.id, option_id=option2.id, user_id=admin.id)
    db.session.add(vote1)
    db.session.add(vote2)
    db.session.commit()
    
    print(f"✅ Vote créé avec {Vote.query.count()} votes")
    
    # Lecture en cours
    reading = ReadingSession(
        book_id=book3.id,
        start_date=datetime.now() - timedelta(days=5),
        end_date=datetime.now() + timedelta(days=25),
        description="Lecture du Hobbit",
        status='current',
        created_by=admin.id
    )
    db.session.add(reading)
    db.session.commit()
    
    print(f"✅ Lecture créée: {ReadingSession.query.count()}")
    
    print("\n🎉 Données de test créées avec succès !")
    print(f"📊 Total: {User.query.count()} utilisateurs, {BookProposal.query.count()} livres, {VotingSession.query.count()} votes, {ReadingSession.query.count()} lectures")
