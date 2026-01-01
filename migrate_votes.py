#!/usr/bin/env python3
"""
Script de migration pour supprimer la contrainte d'unicité sur les votes
et permettre les votes multiples dans BiblioRuche
"""

import os
import sys
import sqlite3

def migrate_database():
    """Supprime la contrainte d'unicité sur les votes pour permettre les votes multiples"""
    
    db_path = os.path.join('instance', 'biblioruche.db')
    
    if not os.path.exists(db_path):
        print("❌ Base de données non trouvée. Assurez-vous que l'application a été initialisée.")
        return False
    
    try:
        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si la contrainte existe
        cursor.execute("PRAGMA table_info(vote)")
        columns = cursor.fetchall()
        
        # Vérifier les contraintes existantes
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='vote'")
        table_def = cursor.fetchone()
        
        if table_def and '_user_voting_session_uc' in table_def[0]:
            print("🔄 Suppression de la contrainte d'unicité sur les votes...")
            
            # Sauvegarder les données existantes
            cursor.execute("SELECT * FROM vote")
            existing_votes = cursor.fetchall()
            
            # Supprimer l'ancienne table
            cursor.execute("DROP TABLE vote")
            
            # Recréer la table sans la contrainte d'unicité
            cursor.execute("""
                CREATE TABLE vote (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    voting_session_id INTEGER NOT NULL,
                    vote_option_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user (id),
                    FOREIGN KEY (voting_session_id) REFERENCES voting_session (id),
                    FOREIGN KEY (vote_option_id) REFERENCES vote_option (id)
                )
            """)
            
            # Restaurer les données
            if existing_votes:
                cursor.executemany(
                    "INSERT INTO vote (id, user_id, voting_session_id, vote_option_id, created_at) VALUES (?, ?, ?, ?, ?)",
                    existing_votes
                )
            
            conn.commit()
            print("✅ Contrainte d'unicité supprimée avec succès!")
            print(f"📊 {len(existing_votes)} votes existants préservés")
            
        else:
            print("ℹ️  Aucune contrainte d'unicité trouvée sur la table vote")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Migration BiblioRuche - Suppression contrainte votes multiples")
    print("="*60)
    
    success = migrate_database()
    
    if success:
        print("\n🎉 Migration terminée avec succès!")
        print("\nLes utilisateurs peuvent maintenant:")
        print("- Voter plusieurs fois dans la même session")
        print("- Les administrateurs peuvent ajouter des livres directement lors de la programmation")
    else:
        print("\n💥 La migration a échoué.")
        sys.exit(1)
