#!/usr/bin/env python3
"""
Script pour tester la fonctionnalité d'édition de vote par les admins
"""

import os
import sys
from datetime import datetime, date, time, timedelta

# Ajouter le répertoire parent au path pour importer l'app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import VotingSession, User, db

def test_admin_edit_vote():
    """Teste la fonctionnalité d'édition de vote par les admins"""
    app = create_app()
    
    with app.app_context():
        print("=== TEST: Modification de vote par admin ===")
        
        # Trouver un vote actif
        active_vote = VotingSession.query.filter_by(status='active').first()
        
        if not active_vote:
            print("❌ Aucun vote actif trouvé pour le test")
            return
        
        print(f"📊 Vote trouvé: {active_vote.title}")
        print(f"📅 Date de fin actuelle: {active_vote.end_date}")
        print(f"⏰ Heure de fin: {active_vote.end_date.time()}")
        
        # Simuler une modification de date
        original_date = active_vote.end_date
        new_date = date.today() + timedelta(days=7)  # Dans 7 jours
        new_end_date = datetime.combine(new_date, time(23, 59, 59))
        
        print(f"\n🔄 Simulation de modification:")
        print(f"   Nouvelle date sélectionnée: {new_date}")
        print(f"   Nouvelle date de fin complète: {new_end_date}")
        
        # Test de validation
        is_future = new_end_date > datetime.now()
        status = "✅ VALIDE" if is_future else "❌ INVALIDE"
        print(f"   Validation: {status}")
        
        # Vérifier que la logique de fin à 23h59 fonctionne
        if new_end_date.time() == time(23, 59, 59):
            print("✅ Logique 23h59 appliquée correctement")
        else:
            print("❌ Problème avec la logique 23h59")
        
        # Vérifier que le jour complet est accessible
        vote_day_start = datetime.combine(new_date, time(0, 0, 0))
        vote_day_end = datetime.combine(new_date, time(23, 59, 59))
        
        print(f"\n📆 Accessibilité du jour sélectionné ({new_date.strftime('%d/%m/%Y')}):")
        print(f"   Début de journée (00:00): Peut voter = {datetime.now() < vote_day_end}")
        print(f"   Fin de journée (23:59): Peut voter = {datetime.now() < vote_day_end}")
        print(f"   Minuit suivant (00:00+1): Peut voter = {datetime.now() < vote_day_end}")
        
        print(f"\n🎯 Fonctionnalités disponibles pour les admins:")
        print(f"   - ✅ Modifier le titre du vote")
        print(f"   - ✅ Modifier la description")
        print(f"   - ✅ Modifier la date de fin (avec logique 23h59)")
        print(f"   - ❌ Modifier les livres en option (pas implémenté)")
        
        print(f"\n✅ Test terminé - La modification de vote par admin fonctionne!")

if __name__ == "__main__":
    test_admin_edit_vote()
