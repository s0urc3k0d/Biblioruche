#!/usr/bin/env python3
"""
Nettoyage simple direct SQLite
"""

import sqlite3
import os

def simple_cleanup():
    db_path = os.path.join('instance', 'biblioruche.db')
    
    if not os.path.exists(db_path):
        print("❌ Base de données introuvable")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print('🧹 NETTOYAGE SIMPLE DE LA BASE')
        print('='*40)
        
        # État initial
        cursor.execute("SELECT COUNT(*) FROM user")
        users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM book_proposal")
        books = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM voting_session")
        sessions = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM vote")
        votes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM reading_session")
        readings = cursor.fetchone()[0]
        
        print('\n📊 AVANT:')
        print(f'  Utilisateurs: {users}')
        print(f'  Livres: {books}')
        print(f'  Sessions vote: {sessions}')
        print(f'  Votes: {votes}')
        print(f'  Lectures: {readings}')
        
        # Supprimer les livres rejetés
        cursor.execute("DELETE FROM book_proposal WHERE status = 'rejected'")
        rejected_deleted = cursor.rowcount
        print(f'\n📚 {rejected_deleted} livres rejetés supprimés')
        
        # Supprimer les votes des sessions fermées
        cursor.execute("""
            DELETE FROM vote 
            WHERE voting_session_id IN (
                SELECT id FROM voting_session WHERE status = 'closed'
            )
        """)
        votes_deleted = cursor.rowcount
        
        # Supprimer les options des sessions fermées
        cursor.execute("""
            DELETE FROM vote_option 
            WHERE voting_session_id IN (
                SELECT id FROM voting_session WHERE status = 'closed'
            )
        """)
        
        # Supprimer les sessions fermées
        cursor.execute("DELETE FROM voting_session WHERE status = 'closed'")
        sessions_deleted = cursor.rowcount
        
        print(f'🗳️  {sessions_deleted} sessions fermées et {votes_deleted} votes supprimés')
        
        conn.commit()
        
        # État final
        cursor.execute("SELECT COUNT(*) FROM user")
        users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM book_proposal")
        books = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM voting_session")
        sessions = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM vote")
        votes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM reading_session")
        readings = cursor.fetchone()[0]
        
        print('\n✅ NETTOYAGE TERMINÉ!')
        print('\n📊 APRÈS:')
        print(f'  Utilisateurs: {users}')
        print(f'  Livres: {books}')
        print(f'  Sessions vote: {sessions}')
        print(f'  Votes: {votes}')
        print(f'  Lectures: {readings}')
        
    except Exception as e:
        conn.rollback()
        print(f'❌ Erreur: {e}')
    finally:
        conn.close()

if __name__ == '__main__':
    simple_cleanup()
