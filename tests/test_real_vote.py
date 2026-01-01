#!/usr/bin/env python3
"""
Script pour tester la correction en créant un vote réel
"""

import os
import sys
from datetime import datetime, date, time

# Ajouter le répertoire parent au path pour importer l'app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import VotingSession, VoteOption, BookProposal, User, db

def test_real_vote_creation():
    """Teste la création d'un vote réel avec la nouvelle logique"""
    app = create_app()
    
    with app.app_context():
        print("=== TEST: Création d'un vote réel ===")
        
        # Vérifier qu'il y a des livres approuvés
        approved_books = BookProposal.query.filter_by(status='approved').all()
        if not approved_books:
            print("❌ Aucun livre approuvé trouvé. Création d'un livre de test...")
            
            # Créer un utilisateur admin si nécessaire
            admin = User.query.filter_by(is_admin=True).first()
            if not admin:
                print("❌ Aucun admin trouvé")
                return
            
            # Créer un livre de test
            test_book = BookProposal(
                title="Test Book - Correction Date",
                author="Test Author",
                description="Livre de test pour valider la correction de date",
                status='approved',
                user_id=admin.id
            )
            db.session.add(test_book)
            db.session.commit()
            approved_books = [test_book]
            print(f"✅ Livre de test créé: {test_book.title}")
        
        # Simuler la création d'un vote avec la date d'aujourd'hui
        test_date = date.today()
        
        # Utiliser la nouvelle logique
        end_date_with_time = datetime.combine(test_date, time(23, 59, 59))
        
        # Créer le vote de test
        admin = User.query.filter_by(is_admin=True).first()
        test_vote = VotingSession(
            title=f"Test Vote - Correction Date {test_date.strftime('%d/%m/%Y')}",
            description="Vote de test pour valider la correction de la logique de fin de vote",
            end_date=end_date_with_time,
            created_by=admin.id
        )
        
        db.session.add(test_vote)
        db.session.flush()
        
        # Ajouter une option de vote
        vote_option = VoteOption(
            voting_session_id=test_vote.id,
            book_id=approved_books[0].id
        )
        db.session.add(vote_option)
        db.session.commit()
        
        print(f"✅ Vote de test créé:")
        print(f"   ID: {test_vote.id}")
        print(f"   Titre: {test_vote.title}")
        print(f"   Date sélectionnée: {test_date.strftime('%d/%m/%Y')}")
        print(f"   Date de fin complète: {test_vote.end_date}")
        print(f"   Statut: {test_vote.status}")
        
        # Vérifier si le vote est encore actif
        now = datetime.now()
        is_active = now <= test_vote.end_date
        print(f"   Maintenant: {now}")
        print(f"   Vote actif: {'🟢 OUI' if is_active else '🔴 NON'}")
        
        if is_active:
            print(f"✅ SUCCÈS: Le vote est actif jusqu'à 23h59 aujourd'hui!")
        else:
            print(f"❌ ÉCHEC: Le vote n'est pas actif")
        
        # Nettoyer le vote de test
        db.session.delete(test_vote)
        db.session.delete(vote_option)
        db.session.commit()
        print(f"🧹 Vote de test supprimé")

if __name__ == "__main__":
    test_real_vote_creation()
