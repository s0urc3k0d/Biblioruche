#!/usr/bin/env python3
"""
Script de démonstration du système de badges BiblioRuche
Crée des données de test et démontre l'attribution des badges
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Badge, UserBadge, BookProposal, BookReview, ReadingParticipation, Vote, Book, ReadingSession, VotingSession, VoteOption
from app.badge_manager import BadgeManager
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def create_demo_user_and_activities():
    """Crée un utilisateur de démonstration avec des activités"""
    app = create_app()
    
    with app.app_context():
        print("🎭 DÉMONSTRATION DU SYSTÈME DE BADGES")
        print("=" * 50)
        
        # Créer un utilisateur de test
        demo_user = User.query.filter_by(username='demo_badges').first()
        if not demo_user:
            demo_user = User(
                username='demo_badges',
                email='demo@badges.com',
                password_hash=generate_password_hash('demo123'),
                display_name='Démo Badges'
            )
            db.session.add(demo_user)
            db.session.commit()
            print(f"✅ Utilisateur de démonstration créé: {demo_user.username}")
        else:
            print(f"ℹ️  Utilisateur de démonstration existant: {demo_user.username}")
        
        # Vérifier les badges initiaux
        initial_badges = UserBadge.query.filter_by(user_id=demo_user.id).count()
        print(f"🏆 Badges initiaux: {initial_badges}")
        
        # 1. Créer des propositions de livres (pour gagner des badges de proposition)
        print(f"\n📚 SIMULATION: Propositions de livres...")
        for i in range(3):
            proposal = BookProposal(
                title=f"Livre Demo {i+1}",
                author=f"Auteur Demo {i+1}",
                description=f"Description du livre de démonstration {i+1}",
                isbn=f"978-0-00000-00{i+1}-0",
                publisher="Éditions Demo",
                publication_year=2024,
                pages_count=200 + i*50,
                genre="Fiction",
                proposed_by=demo_user.id,
                status='accepted'  # Acceptées pour compter
            )
            db.session.add(proposal)
        
        db.session.commit()
        print(f"   ✅ 3 propositions acceptées créées")
        
        # Vérifier l'attribution automatique après propositions
        awarded_badges = BadgeManager.check_and_award_badges(demo_user.id)
        if awarded_badges:
            badge_names = [badge.name for badge in awarded_badges]
            print(f"   🏆 Badges obtenus: {', '.join(badge_names)}")
        
        # 2. Créer des avis (pour gagner des badges d'avis)
        print(f"\n⭐ SIMULATION: Avis sur livres...")
        
        # Créer quelques livres s'ils n'existent pas
        books = Book.query.limit(3).all()
        if len(books) < 3:
            for i in range(3 - len(books)):
                book = Book(
                    title=f"Livre Test {i+1}",
                    author=f"Auteur Test {i+1}",
                    isbn=f"978-1-11111-11{i+1}-0",
                    publisher="Test Publisher",
                    publication_year=2023,
                    pages_count=300,
                    genre="Test"
                )
                db.session.add(book)
            db.session.commit()
            books = Book.query.limit(3).all()
        
        # Créer des avis
        for i, book in enumerate(books):
            existing_review = BookReview.query.filter_by(user_id=demo_user.id, book_id=book.id).first()
            if not existing_review:
                review = BookReview(
                    user_id=demo_user.id,
                    book_id=book.id,
                    rating=4 + i % 2,  # Alternance entre 4 et 5 étoiles
                    comment=f"Excellent livre ! Avis de démonstration {i+1}"
                )
                db.session.add(review)
        
        db.session.commit()
        print(f"   ✅ Avis créés")
        
        # Vérifier l'attribution automatique après avis
        awarded_badges = BadgeManager.check_and_award_badges(demo_user.id)
        if awarded_badges:
            badge_names = [badge.name for badge in awarded_badges]
            print(f"   🏆 Badges obtenus: {', '.join(badge_names)}")
        
        # 3. Créer des participations aux lectures
        print(f"\n📖 SIMULATION: Participations aux lectures...")
        
        # Créer des sessions de lecture s'il n'y en a pas
        reading_sessions = ReadingSession.query.limit(2).all()
        if len(reading_sessions) < 2:
            for i, book in enumerate(books[:2]):
                session = ReadingSession(
                    book_id=book.id,
                    title=f"Lecture collective: {book.title}",
                    description=f"Session de lecture démonstration {i+1}",
                    start_date=datetime.now() - timedelta(days=30),
                    end_date=datetime.now() + timedelta(days=30),
                    status='active'
                )
                db.session.add(session)
            db.session.commit()
            reading_sessions = ReadingSession.query.limit(2).all()
        
        # Créer des participations
        for session in reading_sessions:
            existing_participation = ReadingParticipation.query.filter_by(
                user_id=demo_user.id, 
                reading_session_id=session.id
            ).first()
            if not existing_participation:
                participation = ReadingParticipation(
                    user_id=demo_user.id,
                    reading_session_id=session.id
                )
                db.session.add(participation)
        
        db.session.commit()
        print(f"   ✅ Participations aux lectures créées")
        
        # Vérifier l'attribution automatique après lectures
        awarded_badges = BadgeManager.check_and_award_badges(demo_user.id)
        if awarded_badges:
            badge_names = [badge.name for badge in awarded_badges]
            print(f"   🏆 Badges obtenus: {', '.join(badge_names)}")
        
        # 4. Afficher le résumé final
        print(f"\n📊 RÉSUMÉ FINAL POUR {demo_user.username}:")
        
        final_proposals = BookProposal.query.filter_by(proposed_by=demo_user.id, status='accepted').count()
        final_reviews = BookReview.query.filter_by(user_id=demo_user.id).count()
        final_readings = ReadingParticipation.query.filter_by(user_id=demo_user.id).count()
        final_votes = Vote.query.filter_by(user_id=demo_user.id).count()
        final_badges = UserBadge.query.filter_by(user_id=demo_user.id).count()
        
        print(f"   📚 Propositions acceptées: {final_proposals}")
        print(f"   ⭐ Avis donnés: {final_reviews}")
        print(f"   📖 Lectures participées: {final_readings}")
        print(f"   🗳️  Votes effectués: {final_votes}")
        print(f"   🏆 Total badges: {final_badges}")
        
        # Lister tous les badges obtenus
        user_badges = UserBadge.query.filter_by(user_id=demo_user.id).all()
        if user_badges:
            print(f"\n🏆 BADGES OBTENUS:")
            for user_badge in user_badges:
                badge = Badge.query.get(user_badge.badge_id)
                print(f"   {badge.icon} {badge.name}")
                print(f"      {badge.description}")
                print(f"      Obtenu le: {user_badge.awarded_at.strftime('%d/%m/%Y à %H:%M')}")
                print()
        
        print("🎉 Démonstration terminée ! L'utilisateur peut maintenant voir ses badges sur son profil.")
        print(f"🌐 Visitez: http://localhost:5000/profile pour voir le profil de l'utilisateur connecté")
        print(f"🌐 Ou: http://localhost:5000/user/{demo_user.id} pour voir le profil de démonstration")

if __name__ == '__main__':
    create_demo_user_and_activities()
