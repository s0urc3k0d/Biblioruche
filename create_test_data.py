#!/usr/bin/env python3
"""
Script pour créer des données de test pour BiblioRuche
"""

from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, BookProposal, VotingSession, VoteOption, Vote, ReadingSession

def create_test_data():
    app = create_app()
    
    with app.app_context():
        # Nettoyer les données existantes
        db.drop_all()
        db.create_all()
        
        print("🗃️ Création des données de test...")
        
        # Créer des utilisateurs de test
        admin_user = User(
            twitch_id='wenyn_123',
            username='wenyn',
            display_name='Wenyn',
            email='wenyn@example.com',
            avatar_url='https://static-cdn.jtvnw.net/jtv_user_pictures/wenyn-profile_image-300x300.png',
            is_admin=True
        )
        
        admin_user2 = User(
            twitch_id='lantredesilver_456',
            username='lantredesilver',
            display_name='LantreDeSilver',
            email='lantredesilver@example.com',
            avatar_url='https://static-cdn.jtvnw.net/jtv_user_pictures/lantredesilver-profile_image-300x300.png',
            is_admin=True
        )
        
        # Utilisateurs normaux
        users = [
            User(
                twitch_id='reader1_789',
                username='bookworm42',
                display_name='BookWorm42',
                email='reader1@example.com',
                avatar_url='',
                is_admin=False
            ),
            User(
                twitch_id='reader2_101',
                username='literaturefan',
                display_name='LiteratureFan',
                email='reader2@example.com',
                avatar_url='',
                is_admin=False
            ),
            User(
                twitch_id='reader3_112',
                username='novelreader',
                display_name='NovelReader',
                email='reader3@example.com',
                avatar_url='',
                is_admin=False
            )
        ]
        
        db.session.add(admin_user)
        db.session.add(admin_user2)
        for user in users:
            db.session.add(user)
        db.session.commit()
        
        print(f"✅ {len(users) + 2} utilisateurs créés")
        
        # Créer des propositions de livres
        books = [
            BookProposal(
                title="Le Nom du Vent",
                author="Patrick Rothfuss",
                isbn="9782841727803",
                description="Premier tome de la Chronique du Tueur de Roi. L'histoire de Kvothe, un héros légendaire.",
                genre="Fantasy",
                page_count=650,
                difficulty_level="intermediate",
                proposed_by=users[0].id,
                status='pending'
            ),
            BookProposal(
                title="Dune",
                author="Frank Herbert",
                isbn="9782266320725",
                description="Chef-d'œuvre de la science-fiction, l'histoire de Paul Atréides sur la planète Arrakis.",
                genre="Science-Fiction",
                page_count=688,
                difficulty_level="advanced",
                proposed_by=users[1].id,
                status='pending'
            ),
            BookProposal(
                title="L'Assassin Royal - L'Apprenti Assassin",
                author="Robin Hobb",
                isbn="9782756406619",
                description="Premier tome de la trilogie de l'Assassin Royal. L'histoire de FitzChevalerie Loinvoyant.",
                genre="Fantasy",
                page_count=480,
                difficulty_level="beginner",
                proposed_by=users[2].id,
                status='pending'
            ),
            BookProposal(
                title="Fondation",
                author="Isaac Asimov",
                isbn="9782070360260",
                description="Premier tome du cycle de Fondation. L'épopée de Hari Seldon et de la psychohistoire.",
                genre="Science-Fiction",
                page_count="320",
                difficulty_level="intermediate",
                proposed_by=admin_user.id,
                status='approved'
            ),
            BookProposal(
                title="Le Hobbit",
                author="J.R.R. Tolkien",
                isbn="9782253049418",
                description="Les aventures de Bilbon Sacquet dans la Terre du Milieu.",
                genre="Fantasy",
                page_count=310,
                difficulty_level="beginner",
                proposed_by=users[0].id,
                status='selected'
            ),
            BookProposal(
                title="1984",
                author="George Orwell",
                isbn="9782070368228",
                description="Dystopie célèbre décrivant une société totalitaire.",
                genre="Dystopie",
                page_count=350,
                difficulty_level="intermediate",
                proposed_by=admin_user2.id,
                status='completed'
            )
        ]
        
        for book in books:
            db.session.add(book)
        db.session.commit()
        
        print(f"✅ {len(books)} propositions de livres créées")
        
        # Créer une session de vote active
        vote_session = VotingSession(
            title="Choix du livre pour Juin 2025",
            description="Votez pour le livre que nous lirons ensemble en juin !",
            start_date=datetime.now() - timedelta(days=2),
            end_date=datetime.now() + timedelta(days=5),
            created_by=admin_user.id,
            status='active'
        )
        db.session.add(vote_session)
        db.session.commit()
        
        # Créer des options de vote
        approved_books = [book for book in books if book.status == 'approved' or book.status == 'pending'][:3]
        vote_options = []
        for book in approved_books:
            option = VoteOption(
                voting_session_id=vote_session.id,
                book_id=book.id
            )
            vote_options.append(option)
            db.session.add(option)
        db.session.commit()
        
        # Créer des votes
        votes = [
            Vote(voting_session_id=vote_session.id, option_id=vote_options[0].id, user_id=users[0].id),
            Vote(voting_session_id=vote_session.id, option_id=vote_options[0].id, user_id=users[1].id),
            Vote(voting_session_id=vote_session.id, option_id=vote_options[1].id, user_id=users[2].id),
            Vote(voting_session_id=vote_session.id, option_id=vote_options[2].id, user_id=admin_user.id),
        ]
        
        for vote in votes:
            db.session.add(vote)
        db.session.commit()
        
        print(f"✅ Session de vote active créée avec {len(votes)} votes")
        
        # Créer une session de vote terminée
        closed_vote = VotingSession(
            title="Livre de Mai 2025 - TERMINÉ",
            description="Vote terminé - Le Hobbit a gagné !",
            start_date=datetime.now() - timedelta(days=20),
            end_date=datetime.now() - timedelta(days=10),
            created_by=admin_user2.id,
            status='closed',
            winner_book_id=books[4].id  # Le Hobbit
        )
        db.session.add(closed_vote)
        db.session.commit()
        
        print("✅ Session de vote terminée créée")
        
        # Créer des sessions de lecture
        current_reading = ReadingSession(
            book_id=books[4].id,  # Le Hobbit
            start_date=datetime.now() - timedelta(days=5),
            end_date=datetime.now() + timedelta(days=25),
            debrief_date=datetime.now() + timedelta(days=30),
            description="Lecture commune du Hobbit - Première aventure de Bilbon !",
            status='current',
            created_by=admin_user.id
        )
        
        upcoming_reading = ReadingSession(
            book_id=books[3].id,  # Fondation
            start_date=datetime.now() + timedelta(days=35),
            end_date=datetime.now() + timedelta(days=65),
            debrief_date=datetime.now() + timedelta(days=70),
            description="Lecture de Fondation - Découvrons la psychohistoire d'Asimov !",
            status='upcoming',
            created_by=admin_user2.id
        )
        
        completed_reading = ReadingSession(
            book_id=books[5].id,  # 1984
            start_date=datetime.now() - timedelta(days=60),
            end_date=datetime.now() - timedelta(days=30),
            debrief_date=datetime.now() - timedelta(days=25),
            description="Lecture de 1984 - Une dystopie terrifiante mais nécessaire.",
            status='completed',
            created_by=admin_user.id
        )
        
        db.session.add(current_reading)
        db.session.add(upcoming_reading)
        db.session.add(completed_reading)
        db.session.commit()
        
        print("✅ 3 sessions de lecture créées (en cours, à venir, terminée)")
        
        print("\n🎉 Données de test créées avec succès !")
        print("\n📊 Résumé :")
        print(f"   👥 {User.query.count()} utilisateurs")
        print(f"   📚 {BookProposal.query.count()} propositions de livres")
        print(f"   🗳️ {VotingSession.query.count()} sessions de vote")
        print(f"   📖 {ReadingSession.query.count()} sessions de lecture")
        print(f"   ✅ {Vote.query.count()} votes exprimés")

if __name__ == '__main__':
    create_test_data()
