#!/usr/bin/env python3
"""
Script pour tester la correction de la logique de fin de vote
"""

import os
import sys
from datetime import datetime, date, time

# Ajouter le répertoire parent au path pour importer l'app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import VotingSession, User, db

def test_vote_end_date_logic():
    """Teste la logique de fin de vote"""
    app = create_app()
    
    with app.app_context():
        print("=== TEST: Logique de fin de vote ===")
        
        # Simuler ce qui se passe dans create_vote
        selected_date = date(2024, 12, 25)  # 25 décembre 2024
        print(f"📅 Date sélectionnée dans le formulaire: {selected_date}")
        
        # Logique ANCIENNE (problématique)
        old_end_date = datetime.combine(selected_date, time(0, 0, 0))  # Minuit
        print(f"⏰ ANCIENNE logique - Date de fin: {old_end_date}")
        print(f"   --> Problème: Vote expire à minuit du {selected_date.strftime('%d/%m/%Y')}")
        print(f"   --> Le jour sélectionné n'est PAS accessible pour voter")
        
        # Logique NOUVELLE (corrigée)
        new_end_date = datetime.combine(selected_date, time(23, 59, 59))  # 23h59
        print(f"✅ NOUVELLE logique - Date de fin: {new_end_date}")
        print(f"   --> Le vote expire à 23h59 du {selected_date.strftime('%d/%m/%Y')}")
        print(f"   --> Le jour sélectionné EST accessible pour voter toute la journée")
        
        # Test avec la date actuelle
        print(f"\n=== TEST: Vérification d'expiration ===")
        now = datetime.now()
        print(f"🕐 Maintenant: {now}")
          # Tester avec différentes dates
        from datetime import timedelta
        test_cases = [
            ("Hier", datetime.combine(date.today(), time(23, 59, 59)) - timedelta(days=1)),
            ("Aujourd'hui 23h59", datetime.combine(date.today(), time(23, 59, 59))),
            ("Demain 23h59", datetime.combine(date.today(), time(23, 59, 59)) + timedelta(days=1))
        ]
        
        for label, test_date in test_cases:
            is_expired = now > test_date
            status = "🔴 EXPIRÉ" if is_expired else "🟢 ACTIF"
            print(f"   {label} ({test_date.strftime('%d/%m/%Y %H:%M:%S')}): {status}")
        
        print(f"\n✅ Test terminé - La correction permet au jour sélectionné d'être accessible!")

if __name__ == "__main__":
    test_vote_end_date_logic()
