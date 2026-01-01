#!/usr/bin/env python3
"""
Script robuste pour créer des données de test pour BiblioRuche
"""
import sys
import os
from datetime import datetime, timedelta

# Ajouter le répertoire parent au path pour importer l'app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_data():
    """Créer des données de test complètes"""
    try:
        from app import create_app, db
        from app.models import User, BookProposal, VotingSession, VoteOption, Vote, ReadingSession
        
        app = create_app()
        
        with app.app_context():
            print("🧹 Nettoyage de la base de données...")
            
            # Supprimer toutes les données existantes (optionnel)
            # db.drop_all()
            # db.create_all()
            
            print("👥 Création des utilisateurs de test...")
            
            # Vérifier si les utilisateurs existent déjà
            if not User.query.filter_by(username='admintest').first():
                admin_user = User(
                    twitch_id='admin123',
                    username='admintest',
                    display_name='Admin Test',
                    email='admin@test.com',
                    avatar_url='https://via.placeholder.com/150x150/007bff/ffffff?text=AT',
                    is_admin=True
                )
                db.session.add(admin_user)
            
            if not User.query.filter_by(username='lecteur1').first():
                reader1 = User(
                    twitch_id='reader123',
                    username='lecteur1',
                    display_name='Lecteur Passionné',
                    email='lecteur1@test.com',
                    avatar_url='https://via.placeholder.com/150x150/28a745/ffffff?text=LP',
                    is_admin=False
                )
                db.session.add(reader1)
            
            if not User.query.filter_by(username='bouquineur').first():
                reader2 = User(
                    twitch_id='reader456',
                    username='bouquineur',
                    display_name='Le Bouquineur',
                    email='bouquineur@test.com',
                    avatar_url='https://via.placeholder.com/150x150/dc3545/ffffff?text=LB',
                    is_admin=False
                )
                db.session.add(reader2)
            
            db.session.commit()
            
            # Récupérer les utilisateurs
            admin_user = User.query.filter_by(username='admintest').first()
            reader1 = User.query.filter_by(username='lecteur1').first()
            reader2 = User.query.filter_by(username='bouquineur').first()
            
            print("📚 Création des propositions de livres...")
              # Créer des propositions de livres si elles n'existent pas
            books_data = [
                {
                    'title': 'Le Seigneur des Anneaux - La Communauté de l\'Anneau',
                    'author': 'J.R.R. Tolkien',
                    'description': 'Premier tome de l\'épique trilogie fantasy qui a défini le genre. Suivez Frodo et ses compagnons dans leur quête pour détruire l\'Anneau Unique.',
                    'isbn': '9782266154612',
                    'publisher': 'Pocket',
                    'publication_year': 1954,
                    'pages_count': 576,
                    'proposed_by': reader1.id,
                    'status': 'pending'
                },
                {
                    'title': 'Dune',
                    'author': 'Frank Herbert',
                    'description': 'Un chef-d\'œuvre de science-fiction qui explore les thèmes du pouvoir, de la religion et de l\'écologie sur la planète désertique d\'Arrakis.',
                    'isbn': '9782266320420',
                    'publisher': 'Pocket',
                    'publication_year': 1965,
                    'pages_count': 688,
                    'proposed_by': reader2.id,
                    'status': 'approved'
                },
                {
                    'title': '1984',
                    'author': 'George Orwell',
                    'description': 'Un roman dystopique prophétique sur la surveillance, la manipulation et le totalitarisme dans une société future.',
                    'isbn': '9782070368228',
                    'publisher': 'Gallimard',
                    'publication_year': 1949,
                    'pages_count': 368,
                    'proposed_by': reader1.id,
                    'status': 'approved'
                },
                {
                    'title': 'Le Nom du Vent',
                    'author': 'Patrick Rothfuss',
                    'description': 'Premier tome de la Chronique du Tueur de Roi. L\'histoire de Kvothe, un héros légendaire qui raconte sa propre histoire.',
                    'isbn': '9782352943754',
                    'publisher': 'Bragelonne',
                    'publication_year': 2007,
                    'pages_count': 661,
                    'proposed_by': reader2.id,
                    'status': 'selected'
                },
                {
                    'title': 'Fondation',
                    'author': 'Isaac Asimov',
                    'description': 'Le premier livre du cycle de Fondation, une saga de science-fiction sur la chute et la renaissance de la civilisation galactique.',
                    'isbn': '9782070415335',
                    'publisher': 'Gallimard',
                    'publication_year': 1951,
                    'pages_count': 280,
                    'proposed_by': reader1.id,
                    'status': 'rejected'
                }
            ]
            
            for book_data in books_data:
                if not BookProposal.query.filter_by(title=book_data['title']).first():
                    book = BookProposal(**book_data)
                    db.session.add(book)
            
            db.session.commit()
            
            print("🗳️ Création des sessions de vote...")
              # Créer une session de vote active
            if not VotingSession.query.filter_by(title='Choix du livre de Juin 2025').first():
                voting_session = VotingSession(
                    title='Choix du livre de Juin 2025',
                    description='Votons pour notre prochaine lecture ! Les deux livres finalistes sont tous deux excellents.',
                    start_date=datetime.now() - timedelta(days=2),
                    end_date=datetime.now() + timedelta(days=5),
                    created_by=admin_user.id,
                    status='active'
                )
                db.session.add(voting_session)
                db.session.commit()
                
                # Récupérer les livres approuvés pour le vote
                dune = BookProposal.query.filter_by(title='Dune').first()
                book_1984 = BookProposal.query.filter_by(title='1984').first()
                
                if dune and book_1984:
                    # Créer des options de vote
                    option1 = VoteOption(
                        voting_session_id=voting_session.id,
                        book_id=dune.id
                    )
                    
                    option2 = VoteOption(
                        voting_session_id=voting_session.id,
                        book_id=book_1984.id
                    )
                    
                    db.session.add_all([option1, option2])
                    db.session.commit()
                    
                    # Créer quelques votes
                    vote1 = Vote(
                        user_id=reader1.id,
                        voting_session_id=voting_session.id,
                        vote_option_id=option1.id
                    )
                    
                    vote2 = Vote(
                        user_id=reader2.id,
                        voting_session_id=voting_session.id,
                        vote_option_id=option2.id
                    )
                    
                    vote3 = Vote(
                        user_id=admin_user.id,
                        voting_session_id=voting_session.id,
                        vote_option_id=option1.id
                    )
                    
                    db.session.add_all([vote1, vote2, vote3])
                    db.session.commit()
            
            print("📖 Création des sessions de lecture...")
              # Créer une session de lecture en cours
            selected_book = BookProposal.query.filter_by(status='selected').first()
            if selected_book and not ReadingSession.query.filter_by(book_id=selected_book.id).first():
                reading_session = ReadingSession(
                    book_id=selected_book.id,
                    start_date=datetime.now() - timedelta(days=7),
                    end_date=datetime.now() + timedelta(days=23),
                    description='Notre lecture actuelle ! Rejoignez-nous sur Twitch pour découvrir cette incroyable aventure ensemble.',
                    created_by=admin_user.id,
                    status='current'
                )
                db.session.add(reading_session)
              # Créer une session de lecture planifiée
            future_book = BookProposal.query.filter_by(title='Dune').first()
            if future_book and not ReadingSession.query.filter_by(book_id=future_book.id).first():
                future_reading = ReadingSession(
                    book_id=future_book.id,
                    start_date=datetime.now() + timedelta(days=30),
                    end_date=datetime.now() + timedelta(days=75),
                    description='Notre prochaine grande aventure science-fiction !',
                    created_by=admin_user.id,
                    status='upcoming'
                )
                db.session.add(future_reading)
            
            db.session.commit()
            
            print("\n✅ Données de test créées avec succès !")
            print(f"   👥 {User.query.count()} utilisateurs")
            print(f"   📚 {BookProposal.query.count()} propositions de livres")
            print(f"   🗳️ {VotingSession.query.count()} session(s) de vote")
            print(f"   📊 {Vote.query.count()} votes")
            print(f"   📖 {ReadingSession.query.count()} session(s) de lecture")
            
            # Afficher un résumé détaillé
            print("\n📋 Résumé des données créées :")
            print("   UTILISATEURS:")
            for user in User.query.all():
                role = "Admin" if user.is_admin else "Lecteur"
                print(f"     - {user.display_name} (@{user.username}) [{role}]")
            
            print("   LIVRES:")
            for book in BookProposal.query.all():
                print(f"     - {book.title} par {book.author} [{book.status}]")
            
            print("   VOTES EN COURS:")
            for vote_session in VotingSession.query.filter_by(status='active').all():
                print(f"     - {vote_session.title} ({Vote.query.join(VoteOption).filter_by(voting_session_id=vote_session.id).count()} votes)")
            
            print("   LECTURES:")
            for reading in ReadingSession.query.all():
                print(f"     - {reading.book.title} [{reading.status}]")
            
            print("\n🎉 BiblioRuche est maintenant remplie de données de démonstration !")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création des données de test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    print("🚀 Lancement de la création des données de test...")
    success = create_test_data()
    if success:
        print("\n✨ Script terminé avec succès !")
    else:
        print("\n💥 Échec du script.")
        sys.exit(1)
