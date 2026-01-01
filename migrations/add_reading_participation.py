#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script pour ajouter la table ReadingParticipation
"""

import os
import sys
from datetime import datetime

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import ReadingParticipation

def create_reading_participation_migration():
    """Créer la migration pour la table ReadingParticipation"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Création de la migration pour ReadingParticipation...")
        
        try:
            # Créer toutes les tables (cela créera seulement les tables manquantes)
            db.create_all()
            print("✅ Migration terminée avec succès!")
            print("📋 La table 'reading_participation' a été créée.")
            
            # Vérification que la table existe
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'reading_participation' in tables:
                print("✅ Vérification: La table 'reading_participation' existe bien.")
                
                # Afficher la structure de la table
                columns = inspector.get_columns('reading_participation')
                print("\n📊 Structure de la table:")
                for column in columns:
                    print(f"   - {column['name']}: {column['type']}")
                    
            else:
                print("❌ Erreur: La table 'reading_participation' n'a pas été créée.")
                
        except Exception as e:
            print(f"❌ Erreur lors de la migration: {e}")
            return False
            
    return True

if __name__ == "__main__":
    print("🚀 Démarrage de la migration ReadingParticipation")
    print("=" * 50)
    
    success = create_reading_participation_migration()
    
    if success:
        print("\n🎉 Migration terminée avec succès!")
        print("💡 Vous pouvez maintenant utiliser la fonctionnalité d'inscription aux lectures.")
    else:
        print("\n❌ La migration a échoué.")
        sys.exit(1)
