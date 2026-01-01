#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script pour ajouter le système de badges
"""

import os
import sys
from datetime import datetime

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Badge, UserBadge

def create_badges_migration():
    """Créer la migration pour les tables Badge et UserBadge"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Création de la migration pour le système de badges...")
        
        try:
            # Créer les tables Badge et UserBadge
            db.create_all()
            print("✅ Migration terminée avec succès!")
            print("📋 Les tables 'badge' et 'user_badge' ont été créées.")
            
            # Vérification que les tables existent
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            badges_created = []
            if 'badge' in tables:
                print("✅ Vérification: La table 'badge' existe bien.")
                badges_created.append('badge')
                
            if 'user_badge' in tables:
                print("✅ Vérification: La table 'user_badge' existe bien.")
                badges_created.append('user_badge')
            
            if len(badges_created) == 2:
                print("\n📊 Structure des tables:")
                
                # Table Badge
                columns = inspector.get_columns('badge')
                print("\n   Table 'badge':")
                for column in columns:
                    print(f"     - {column['name']}: {column['type']}")
                
                # Table UserBadge
                columns = inspector.get_columns('user_badge')
                print("\n   Table 'user_badge':")
                for column in columns:
                    print(f"     - {column['name']}: {column['type']}")
                
                # Créer des badges de base
                create_initial_badges()
                
            else:
                print("❌ Erreur: Les tables n'ont pas été créées correctement.")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la migration: {e}")
            return False
            
    return True

def create_initial_badges():
    """Créer des badges initiaux pour le système"""
    print("\n🏆 Création des badges initiaux...")
    
    initial_badges = [
        # Badges de lecture
        {
            'name': 'Premier pas',
            'description': 'Participer à sa première lecture',
            'icon': 'fas fa-baby',
            'category': 'lecture',
            'color': 'success'
        },
        {
            'name': 'Lecteur régulier',
            'description': 'Participer à 5 lectures',
            'icon': 'fas fa-book',
            'category': 'lecture',
            'color': 'primary'
        },
        {
            'name': 'Lecteur assidu',
            'description': 'Participer à 10 lectures',
            'icon': 'fas fa-graduation-cap',
            'category': 'lecture',
            'color': 'warning'
        },
        
        # Badges de notation
        {
            'name': 'Premier avis',
            'description': 'Donner son premier avis sur un livre',
            'icon': 'fas fa-pen',
            'category': 'notation',
            'color': 'info'
        },
        {
            'name': 'Critique actif',
            'description': 'Donner 10 avis avec notes',
            'icon': 'fas fa-star',
            'category': 'notation',
            'color': 'warning'
        },
        
        # Badges de vote
        {
            'name': 'Premier vote',
            'description': 'Participer à son premier vote',
            'icon': 'fas fa-vote-yea',
            'category': 'vote',
            'color': 'success'
        },
        {
            'name': 'Voteur actif',
            'description': 'Participer à 5 votes',
            'icon': 'fas fa-poll',
            'category': 'vote',
            'color': 'primary'
        },
        
        # Badges de proposition
        {
            'name': 'Première proposition',
            'description': 'Proposer son premier livre',
            'icon': 'fas fa-lightbulb',
            'category': 'proposition',
            'color': 'info'
        },
        {
            'name': 'Proposeur',
            'description': '3 propositions acceptées',
            'icon': 'fas fa-trophy',
            'category': 'proposition',
            'color': 'warning'
        },
        {
            'name': 'Découvreur',
            'description': '5 propositions acceptées',
            'icon': 'fas fa-crown',
            'category': 'proposition',
            'color': 'danger'
        }
    ]
    
    created_count = 0
    for badge_data in initial_badges:
        # Vérifier si le badge n'existe pas déjà
        existing = Badge.query.filter_by(name=badge_data['name']).first()
        if not existing:
            badge = Badge(**badge_data)
            db.session.add(badge)
            created_count += 1
            print(f"  ✅ Badge créé: {badge_data['name']}")
    
    db.session.commit()
    print(f"\n🎉 {created_count} badges créés avec succès!")

if __name__ == "__main__":
    print("🚀 Démarrage de la migration du système de badges")
    print("=" * 60)
    
    success = create_badges_migration()
    
    if success:
        print("\n🎉 Migration terminée avec succès!")
        print("💡 Le système de badges est maintenant disponible.")
        print("🏆 Les utilisateurs peuvent maintenant gagner des badges!")
    else:
        print("\n❌ La migration a échoué.")
        sys.exit(1)
