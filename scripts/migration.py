#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import BookReview

def migrate_database():
    app = create_app()
    
    with app.app_context():
        try:
            # Créer la nouvelle table BookReview
            db.create_all()
            print("✅ Table BookReview créée avec succès!")
            
            # Vérifier que la table existe
            result = db.engine.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='book_review';")
            if result.fetchone():
                print("✅ Vérification : Table book_review existe dans la base")
            else:
                raise Exception("❌ Table book_review non trouvée après création")
                
        except Exception as e:
            print(f"❌ Erreur lors de la migration: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("🎉 Migration terminée avec succès!")
        sys.exit(0)
    else:
        print("💥 Échec de la migration!")
        sys.exit(1)
