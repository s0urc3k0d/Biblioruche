#!/usr/bin/env python3
# Script de vérification de la table BookReview

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def verify_table():
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 Vérification de la table book_review...")
            
            # Vérifier si la table existe
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='book_review';"))
            table_exists = result.fetchone()
            
            if not table_exists:
                print("❌ La table book_review n'existe pas!")
                return False
            
            print("✅ Table book_review trouvée")
            
            # Afficher la structure de la table
            structure = db.session.execute(text("PRAGMA table_info(book_review);"))
            columns = structure.fetchall()
            
            print(f"\n📋 Structure de la table ({len(columns)} colonnes):")
            print("-" * 60)
            
            for row in columns:
                col_id, name, col_type, not_null, default_val, pk = row
                pk_marker = " (PK)" if pk else ""
                null_marker = " NOT NULL" if not_null else ""
                default_marker = f" DEFAULT {default_val}" if default_val else ""
                
                print(f"  {name:<15} {col_type:<10}{null_marker}{default_marker}{pk_marker}")
            
            print("-" * 60)
            
            # Vérifier les contraintes
            constraints = db.session.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='book_review';"))
            constraint_sql = constraints.fetchone()
            
            if constraint_sql:
                print(f"\n🔗 Définition complète de la table:")
                print(constraint_sql[0])
            
            # Compter les lignes existantes
            count = db.session.execute(text("SELECT COUNT(*) FROM book_review;"))
            row_count = count.fetchone()[0]
            print(f"\n📊 Nombre d'avis actuels: {row_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la vérification: {e}")
            return False

if __name__ == "__main__":
    success = verify_table()
    if success:
        print("\n✅ Vérification terminée avec succès!")
    else:
        print("\n❌ Échec de la vérification!")
        sys.exit(1)
