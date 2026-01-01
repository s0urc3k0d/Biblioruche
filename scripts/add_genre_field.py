#!/usr/bin/env python3
"""
Script pour ajouter le champ 'genre' à la table BookProposal
"""

import sqlite3
import os
from pathlib import Path

def add_genre_field():
    """Ajouter le champ genre à la table book_proposal"""
    
    # Chemin vers la base de données
    db_path = Path(__file__).parent / "instance" / "biblioruche.db"
    
    if not db_path.exists():
        print(f"❌ Base de données non trouvée: {db_path}")
        return False
    
    try:
        # Connexion à la base de données
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Vérifier si la colonne existe déjà
        cursor.execute("PRAGMA table_info(book_proposal)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"🔍 Colonnes actuelles avant migration: {', '.join(columns)}")
        
        if 'genre' in columns:
            print("✅ Le champ 'genre' existe déjà dans la table book_proposal")
            return True
        
        # Ajouter la colonne genre
        print("🔄 Ajout du champ 'genre' à la table book_proposal...")
        cursor.execute("ALTER TABLE book_proposal ADD COLUMN genre VARCHAR(100)")
        
        # Confirmer les changements
        conn.commit()
        print("💾 Changements sauvegardés")
        
        # Vérification finale
        cursor.execute("PRAGMA table_info(book_proposal)")
        columns_after = [column[1] for column in cursor.fetchall()]
        print(f"📋 Colonnes après migration: {', '.join(columns_after)}")
        
        if 'genre' in columns_after:
            print("✅ Champ 'genre' ajouté avec succès!")
            return True
        else:
            print("❌ Échec de l'ajout du champ 'genre'")
            return False
        
    except sqlite3.Error as e:
        print(f"❌ Erreur SQLite: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Début de la migration: ajout du champ 'genre'")
    success = add_genre_field()
    
    if success:
        print("✅ Migration terminée avec succès!")
    else:
        print("❌ Échec de la migration")
        exit(1)
