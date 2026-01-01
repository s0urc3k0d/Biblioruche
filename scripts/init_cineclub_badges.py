# -*- coding: utf-8 -*-
"""
Script pour initialiser les badges CinéClub dans la base de données
"""

import os
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Badge

CINECLUB_BADGES = [
    {
        "name": "Premier Film",
        "description": "A participé à sa première séance de visionnage CinéClub",
        "icon": "fa-film",
        "category": "cineclub",
        "color": "danger"
    },
    {
        "name": "Cinéphile",
        "description": "A participé à 5 séances de visionnage CinéClub",
        "icon": "fa-video",
        "category": "cineclub",
        "color": "warning"
    },
    {
        "name": "Cinéphile passionné",
        "description": "A participé à 15 séances de visionnage CinéClub",
        "icon": "fa-star",
        "category": "cineclub",
        "color": "danger"
    },
    {
        "name": "Voteur de films",
        "description": "A voté pour son premier film au CinéClub",
        "icon": "fa-check-circle",
        "category": "cineclub",
        "color": "info"
    },
    {
        "name": "Critique de cinéma",
        "description": "A voté pour 10 films au CinéClub",
        "icon": "fa-poll",
        "category": "cineclub",
        "color": "primary"
    },
    {
        "name": "Réalisateur en herbe",
        "description": "A proposé un film qui a été accepté",
        "icon": "fa-clapperboard",
        "category": "cineclub",
        "color": "success"
    },
    {
        "name": "Programmateur",
        "description": "A proposé 5 films acceptés au CinéClub",
        "icon": "fa-trophy",
        "category": "cineclub",
        "color": "warning"
    }
]

def init_cineclub_badges():
    """Initialise les badges CinéClub"""
    app = create_app()
    
    with app.app_context():
        print("🎬 Initialisation des badges CinéClub...")
        
        created = 0
        existing = 0
        
        for badge_data in CINECLUB_BADGES:
            existing_badge = Badge.query.filter_by(name=badge_data["name"]).first()
            
            if existing_badge:
                print(f"  ⏭️  Badge '{badge_data['name']}' existe déjà")
                existing += 1
            else:
                badge = Badge(
                    name=badge_data["name"],
                    description=badge_data["description"],
                    icon=badge_data["icon"],
                    category=badge_data["category"],
                    color=badge_data["color"]
                )
                db.session.add(badge)
                print(f"  ✅ Badge '{badge_data['name']}' créé")
                created += 1
        
        db.session.commit()
        
        print(f"\n📊 Résumé:")
        print(f"   - {created} badges créés")
        print(f"   - {existing} badges existants")
        print(f"   - Total badges CinéClub: {Badge.query.filter_by(category='cineclub').count()}")

if __name__ == '__main__':
    init_cineclub_badges()
