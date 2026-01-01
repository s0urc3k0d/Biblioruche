# -*- coding: utf-8 -*-
"""
Script de migration pour ajouter les tables Ebooks et CinéClub
"""

import os
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import (
    Ebook, CineClubSettings, Film, FilmVotingSession, 
    FilmVoteOption, FilmVote, ViewingSession, ViewingParticipation
)

def migrate():
    """Crée les nouvelles tables pour Ebooks et CinéClub"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Création des nouvelles tables...")
        
        # Créer toutes les tables (y compris les nouvelles)
        db.create_all()
        
        print("✅ Tables créées avec succès !")
        
        # Initialiser les paramètres CinéClub si pas encore fait
        settings = CineClubSettings.query.first()
        if not settings:
            settings = CineClubSettings(
                is_enabled=False,
                module_name='BiblioCinéClub',
                description='Découvrez des films ensemble et partagez vos impressions !'
            )
            db.session.add(settings)
            db.session.commit()
            print("✅ Paramètres CinéClub initialisés (désactivé par défaut)")
        else:
            print("ℹ️  Paramètres CinéClub déjà existants")
        
        print("\n📊 Résumé des tables :")
        print(f"  - Ebook: {Ebook.query.count()} entrées")
        print(f"  - Film: {Film.query.count()} entrées")
        print(f"  - FilmVotingSession: {FilmVotingSession.query.count()} entrées")
        print(f"  - ViewingSession: {ViewingSession.query.count()} entrées")
        print(f"  - CineClubSettings: {'Activé' if settings.is_enabled else 'Désactivé'}")

if __name__ == '__main__':
    migrate()
