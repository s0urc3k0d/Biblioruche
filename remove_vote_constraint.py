"""
Script pour supprimer la contrainte d'unicité sur les votes
afin de permettre les votes multiples par utilisateur
"""

from app import create_app, db
import sqlite3

def remove_vote_constraint():
    app = create_app()
    with app.app_context():
        # Récupérer le chemin de la base de données
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        print(f"Modification de la base de données: {db_path}")
        
        # Se connecter directement à SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # 1. Créer une nouvelle table vote sans la contrainte
            cursor.execute('''
                CREATE TABLE vote_new (
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
            
            # 2. Copier les données existantes
            cursor.execute('''
                INSERT INTO vote_new (id, user_id, voting_session_id, vote_option_id, created_at)
                SELECT id, user_id, voting_session_id, vote_option_id, created_at
                FROM vote
            ''')
            
            # 3. Supprimer l'ancienne table
            cursor.execute('DROP TABLE vote')
            
            # 4. Renommer la nouvelle table
            cursor.execute('ALTER TABLE vote_new RENAME TO vote')
            
            # Valider les changements
            conn.commit()
            print("✅ Contrainte d'unicité supprimée avec succès!")
            print("✅ Les votes multiples sont maintenant autorisés!")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Erreur: {e}")
            raise
        finally:
            conn.close()

if __name__ == "__main__":
    remove_vote_constraint()
