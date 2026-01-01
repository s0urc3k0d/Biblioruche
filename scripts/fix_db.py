import sqlite3

conn = sqlite3.connect('instance/biblioruche.db')
cursor = conn.cursor()

print('=== MODIFICATION TABLE VOTE ===')

try:
    # Créer nouvelle table sans contrainte
    cursor.execute('''
        CREATE TABLE vote_new (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            voting_session_id INTEGER NOT NULL,
            vote_option_id INTEGER NOT NULL,
            created_at DATETIME
        )
    ''')
    print('✓ Table temporaire créée')
    
    # Copier données
    cursor.execute('INSERT INTO vote_new SELECT * FROM vote')
    print('✓ Données copiées')
    
    # Supprimer ancienne table
    cursor.execute('DROP TABLE vote')
    print('✓ Ancienne table supprimée')
    
    # Renommer
    cursor.execute('ALTER TABLE vote_new RENAME TO vote')
    print('✓ Table renommée')
    
    conn.commit()
    print('✅ SUCCÈS: Contrainte supprimée!')
    
except Exception as e:
    print(f'❌ Erreur: {e}')
    conn.rollback()
finally:
    conn.close()
