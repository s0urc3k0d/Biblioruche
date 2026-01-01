#!/usr/bin/env python3
# Script pour ajouter la table BookReview à la base de données

import sys
import os

# Ajouter le répertoire parent au path pour pouvoir importer l'app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import BookReview

def add_review_table():
    app = create_app()
    
    with app.app_context():
        try:
            # Créer la nouvelle table
            db.create_all()
            print("✅ Table BookReview créée avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de la table: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = add_review_table()
    if success:
        print("🎉 Migration terminée avec succès!")
    else:
        print("💥 Échec de la migration!")
        sys.exit(1)
