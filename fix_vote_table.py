import sqlite3
import os
import sys

def fix_vote_constraint():
    """
    Supprime la contrainte d'unicité sur la table vote
    pour permettre les votes multiples
    """
    
    db_path = os.path.join('instance', 'biblioruche.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données introuvable: {db_path}")
        return False
    
    print(f"🔧 Modification de la base de données: {db_path}")
    
    try:
        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("1️⃣ Vérification de la structure actuelle...")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='vote'")
        result = cursor.fetchone()
        if result:
            print(f"   Structure actuelle: {result[0]}")
        
        print("2️⃣ Création de la nouvelle table sans contrainte...")
        cursor.execute('''
            CREATE TABLE vote_temp (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                voting_session_id INTEGER NOT NULL,
                vote_option_id INTEGER NOT NULL,
                created_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES user (id),
                FOREIGN KEY (voting_session_id) REFERENCES voting_session (id),
                FOREIGN KEY (vote_option_id) REFERENCES vote_option (id)
            )
        ''')
        
        print("3️⃣ Copie des données existantes...")
        cursor.execute('''
            INSERT INTO vote_temp (id, user_id, voting_session_id, vote_option_id, created_at)
            SELECT id, user_id, voting_session_id, vote_option_id, created_at
            FROM vote
        ''')
        
        # Vérifier que les données ont été copiées
        cursor.execute("SELECT COUNT(*) FROM vote")
        old_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM vote_temp")
        new_count = cursor.fetchone()[0]
        print(f"   Données copiées: {old_count} → {new_count}")
        
        if old_count != new_count:
            raise Exception("Erreur lors de la copie des données")
        
        print("4️⃣ Suppression de l'ancienne table...")
        cursor.execute('DROP TABLE vote')
        
        print("5️⃣ Renommage de la nouvelle table...")
        cursor.execute('ALTER TABLE vote_temp RENAME TO vote')
        
        print("6️⃣ Validation des changements...")
        conn.commit()
        
        # Vérifier la nouvelle structure
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='vote'")
        result = cursor.fetchone()
        if result:
            print(f"   Nouvelle structure: {result[0]}")
        
        print("✅ SUCCÈS: Contrainte d'unicité supprimée!")
        print("✅ Les votes multiples sont maintenant autorisés!")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        
        # Rollback en cas d'erreur
        try:
            conn.rollback()
        except:
            pass
        
        return False
        
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == "__main__":
    success = fix_vote_constraint()
    sys.exit(0 if success else 1)
