#!/usr/bin/env python3
"""
Script d'attribution rétroactive des badges pour BiblioRuche
Attribue automatiquement les badges aux utilisateurs existants
basé sur leurs activités passées.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Badge, UserBadge
from app.badge_manager import BadgeManager

def run_retroactive_badge_assignment():
    """Exécute l'attribution rétroactive des badges pour tous les utilisateurs"""
    app = create_app()
    
    with app.app_context():
        print("🏆 Début de l'attribution rétroactive des badges...")
        print("=" * 50)
        
        # Récupérer tous les utilisateurs
        users = User.query.all()
        print(f"📊 {len(users)} utilisateur(s) trouvé(s)")
        
        total_badges_awarded = 0
        
        for user in users:
            print(f"\n👤 Traitement de l'utilisateur: {user.username} (ID: {user.id})")
            
            # Vérifier et attribuer les badges
            awarded_badges = BadgeManager.check_and_award_badges(user.id)
            
            if awarded_badges:
                badge_names = [badge.name for badge in awarded_badges]
                print(f"   ✅ {len(awarded_badges)} badge(s) attribué(s): {', '.join(badge_names)}")
                total_badges_awarded += len(awarded_badges)
            else:
                print("   ℹ️  Aucun nouveau badge à attribuer")
        
        print("\n" + "=" * 50)
        print(f"🎉 Attribution terminée !")
        print(f"📈 Total de badges attribués: {total_badges_awarded}")
        
        # Afficher un résumé par badge
        print(f"\n📊 Résumé par badge:")
        badges = Badge.query.all()
        for badge in badges:
            user_count = UserBadge.query.filter_by(badge_id=badge.id).count()
            print(f"   {badge.icon} {badge.name}: {user_count} utilisateur(s)")

if __name__ == '__main__':
    run_retroactive_badge_assignment()
