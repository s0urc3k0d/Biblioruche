import sqlite3
import os

print('🧹 Nettoyage de la base BiblioRuche')

# Connexion à la base
db_path = 'instance/biblioruche.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# État avant
cursor.execute("SELECT COUNT(*) FROM book_proposal")
books_before = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM voting_session")
sessions_before = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM vote")
votes_before = cursor.fetchone()[0]

print(f'Avant: {books_before} livres, {sessions_before} sessions, {votes_before} votes')

# Nettoyage
cursor.execute("DELETE FROM book_proposal WHERE status = 'rejected'")
rejected_books = cursor.rowcount

cursor.execute("DELETE FROM vote WHERE voting_session_id IN (SELECT id FROM voting_session WHERE status = 'closed')")
deleted_votes = cursor.rowcount

cursor.execute("DELETE FROM vote_option WHERE voting_session_id IN (SELECT id FROM voting_session WHERE status = 'closed')")

cursor.execute("DELETE FROM voting_session WHERE status = 'closed'")
deleted_sessions = cursor.rowcount

conn.commit()

# État après
cursor.execute("SELECT COUNT(*) FROM book_proposal")
books_after = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM voting_session")
sessions_after = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM vote")
votes_after = cursor.fetchone()[0]

print(f'Supprimé: {rejected_books} livres rejetés, {deleted_sessions} sessions, {deleted_votes} votes')
print(f'Après: {books_after} livres, {sessions_after} sessions, {votes_after} votes')
print('✅ Nettoyage terminé!')

conn.close()
