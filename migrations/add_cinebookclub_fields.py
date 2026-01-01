"""
Migration: Ajout des champs CinéBookClub au modèle Film
- book_proposal_id: FK vers BookProposal (livre associé)
- platforms: String contenant les plateformes de streaming (séparées par virgules)
"""

import sqlite3
import os
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'biblioruche.db')
    
    if not os.path.exists(db_path):
        print(f"Base de données non trouvée: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Vérifier si la colonne book_proposal_id existe déjà
        cursor.execute("PRAGMA table_info(film)")
        columns = [col[1] for col in cursor.fetchall()]
        
        migrations_done = []
        
        # Ajouter book_proposal_id si nécessaire
        if 'book_proposal_id' not in columns:
            print("Ajout de la colonne 'book_proposal_id' à la table 'film'...")
            cursor.execute("ALTER TABLE film ADD COLUMN book_proposal_id INTEGER REFERENCES book_proposal(id)")
            migrations_done.append('book_proposal_id')
        else:
            print("La colonne 'book_proposal_id' existe déjà.")
        
        # Ajouter platforms si nécessaire
        if 'platforms' not in columns:
            print("Ajout de la colonne 'platforms' à la table 'film'...")
            cursor.execute("ALTER TABLE film ADD COLUMN platforms VARCHAR(500)")
            migrations_done.append('platforms')
        else:
            print("La colonne 'platforms' existe déjà.")
        
        conn.commit()
        
        if migrations_done:
            print(f"\n✅ Migration réussie ! Colonnes ajoutées: {', '.join(migrations_done)}")
        else:
            print("\n✅ Aucune migration nécessaire, toutes les colonnes existent déjà.")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("Migration CinéBookClub - Ajout des champs au modèle Film")
    print("=" * 60)
    migrate()
