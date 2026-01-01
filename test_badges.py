#!/usr/bin/env python3
"""
Script de test du système de badges BiblioRuche
Teste les fonctionnalités de badges et affiche les statistiques
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Badge, UserBadge, BookProposal, BookReview, ReadingParticipation, Vote
from app.badge_manager import BadgeManager

def test_badge_system():
    """Test complet du système de badges"""
    app = create_app()
    
    with app.app_context():
        print("🏆 SYSTÈME DE BADGES BIBLIORUCHE")
        print("=" * 50)
        
        # 1. Afficher les badges disponibles
        print("\n📋 BADGES DISPONIBLES:")
        badges = Badge.query.all()
        if not badges:
            print("   ❌ Aucun badge trouvé ! Exécutez la migration add_badges_system.py")
            return
            
        for badge in badges:
            print(f"   {badge.icon} {badge.name}")
            print(f"      Catégorie: {badge.category}")
            print(f"      Description: {badge.description}")
            print(f"      Condition: {badge.condition}")
            print()
        
        # 2. Afficher les utilisateurs et leurs statistiques
        print("👥 UTILISATEURS ET STATISTIQUES:")
        users = User.query.all()
        if not users:
            print("   ❌ Aucun utilisateur trouvé !")
            return
            
        for user in users:
            print(f"\n👤 {user.username} (ID: {user.id})")
            
            # Statistiques
            proposals_count = BookProposal.query.filter_by(proposed_by=user.id, status='accepted').count()
            reviews_count = BookReview.query.filter_by(user_id=user.id).count()
            readings_count = ReadingParticipation.query.filter_by(user_id=user.id).count()
            votes_count = Vote.query.filter_by(user_id=user.id).count()
            
            print(f"   📚 Propositions acceptées: {proposals_count}")
            print(f"   ⭐ Avis donnés: {reviews_count}")
            print(f"   📖 Lectures participées: {readings_count}")
            print(f"   🗳️  Votes effectués: {votes_count}")
            
            # Badges actuels
            user_badges = UserBadge.query.filter_by(user_id=user.id).all()
            if user_badges:
                print(f"   🏆 Badges ({len(user_badges)}):")
                for user_badge in user_badges:
                    badge = Badge.query.get(user_badge.badge_id)
                    print(f"      {badge.icon} {badge.name} (obtenu le {user_badge.awarded_at.strftime('%d/%m/%Y')})")
            else:
                print("   🏆 Badges: Aucun badge encore obtenu")
        
        # 3. Test d'attribution automatique
        print(f"\n🔧 TEST D'ATTRIBUTION AUTOMATIQUE:")
        total_awarded = 0
        for user in users:
            print(f"   Vérification pour {user.username}...")
            awarded_badges = BadgeManager.check_and_award_badges(user.id)
            if awarded_badges:
                badge_names = [badge.name for badge in awarded_badges]
                print(f"   ✅ {len(awarded_badges)} nouveau(x) badge(s): {', '.join(badge_names)}")
                total_awarded += len(awarded_badges)
            else:
                print(f"   ℹ️  Aucun nouveau badge")
        
        print(f"\n📊 RÉSUMÉ FINAL:")
        print(f"   🏆 Total badges attribués: {total_awarded}")
        print(f"   👥 Utilisateurs traités: {len(users)}")
        
        # Statistiques par badge
        print(f"\n📈 DISTRIBUTION DES BADGES:")
        for badge in badges:
            count = UserBadge.query.filter_by(badge_id=badge.id).count()
            print(f"   {badge.icon} {badge.name}: {count} utilisateur(s)")

if __name__ == '__main__':
    test_badge_system()
