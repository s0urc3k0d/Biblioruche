#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer des données de test pour les participations aux lectures
"""

import os
import sys
from datetime import datetime

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, ReadingSession, ReadingParticipation

def create_test_participations():
    """Créer des participations de test"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Création de participations de test...")
        
        try:
            # Récupérer quelques utilisateurs et lectures
            users = User.query.limit(5).all()
            readings = ReadingSession.query.filter(
                ReadingSession.status.in_(['current', 'upcoming'])
            ).all()
            
            if not users:
                print("❌ Aucun utilisateur trouvé. Veuillez d'abord créer des utilisateurs de test.")
                return False
                
            if not readings:
                print("❌ Aucune lecture trouvée. Veuillez d'abord créer des lectures de test.")
                return False
            
            print(f"👥 {len(users)} utilisateurs trouvés")
            print(f"📚 {len(readings)} lectures trouvées")
            
            # Créer des participations variées
            participations_created = 0
            
            for reading in readings:
                # Faire participer 2-4 utilisateurs par lecture
                import random
                participating_users = random.sample(users, min(random.randint(2, 4), len(users)))
                
                for user in participating_users:
                    # Vérifier si cette participation n'existe pas déjà
                    existing = ReadingParticipation.query.filter_by(
                        user_id=user.id,
                        reading_session_id=reading.id
                    ).first()
                    
                    if not existing:
                        participation = ReadingParticipation(
                            user_id=user.id,
                            reading_session_id=reading.id
                        )
                        db.session.add(participation)
                        participations_created += 1
                        print(f"✅ {user.display_name} inscrit à '{reading.book.title}'")
            
            db.session.commit()
            
            print(f"\n🎉 {participations_created} participations créées avec succès!")
            
            # Afficher un résumé
            print("\n📊 Résumé des participations:")
            for reading in readings:
                count = reading.get_participants_count()
                print(f"   📖 {reading.book.title}: {count} participant{'s' if count != 1 else ''}")
                
        except Exception as e:
            print(f"❌ Erreur lors de la création des participations: {e}")
            db.session.rollback()
            return False
            
    return True

if __name__ == "__main__":
    print("🚀 Création de données de test pour les participations")
    print("=" * 50)
    
    success = create_test_participations()
    
    if success:
        print("\n🎉 Données de test créées avec succès!")
        print("💡 Vous pouvez maintenant tester la fonctionnalité d'inscription aux lectures.")
    else:
        print("\n❌ La création des données de test a échoué.")
        sys.exit(1)
