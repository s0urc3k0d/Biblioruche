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
            
            # Vérifier que la table existe avec la syntaxe moderne de SQLAlchemy
            from sqlalchemy import text
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='book_review';"))
            table_exists = result.fetchone()
            
            if table_exists:
                print("✅ Vérification : Table book_review existe dans la base")
                
                # Vérifier la structure de la table
                structure = db.session.execute(text("PRAGMA table_info(book_review);"))
                columns = structure.fetchall()
                print(f"✅ Structure de la table : {len(columns)} colonnes trouvées")
                
                # Afficher les colonnes pour validation
                expected_columns = ['id', 'user_id', 'book_id', 'rating', 'comment', 'is_moderated', 'is_visible', 'created_at', 'updated_at']
                found_columns = [col[1] for col in columns]  # col[1] est le nom de la colonne
                
                for expected in expected_columns:
                    if expected in found_columns:
                        print(f"  ✅ Colonne '{expected}' présente")
                    else:
                        print(f"  ❌ Colonne '{expected}' manquante")
                        return False
                        
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
        print("📋 La table BookReview est prête à recevoir des avis!")
        sys.exit(0)
    else:
        print("💥 Échec de la migration!")
        sys.exit(1)
