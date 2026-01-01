#!/usr/bin/env python3
"""
Script pour vérifier les données de livres dans la base
"""

import sqlite3
import os

# Chemin vers la base de données
db_path = r'c:\Users\alexa\BiblioRuche\instance\biblioruche.db'

if not os.path.exists(db_path):
    print("❌ Base de données introuvable!")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Vérifier les livres
    cursor.execute("SELECT id, title, author, status FROM book_proposal LIMIT 10")
    books = cursor.fetchall()
    
    print("📚 LIVRES DANS LA BASE:")
    print("=" * 50)
    
    if books:
        for book in books:
            print(f"ID: {book[0]} | {book[1]} par {book[2]} | Statut: {book[3]}")
    else:
        print("Aucun livre trouvé dans la base de données")
    
    print(f"\nTotal des livres: {len(books)}")
    
    # Vérifier les statuts disponibles
    cursor.execute("SELECT DISTINCT status FROM book_proposal")
    statuses = cursor.fetchall()
    print(f"\nStatuts des livres: {[s[0] for s in statuses]}")
    
    conn.close()
    print("\n✅ Test terminé avec succès!")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
