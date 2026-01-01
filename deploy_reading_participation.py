#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migration pour déployer la fonctionnalité d'inscription aux lectures en production
"""

import os
import sys
from datetime import datetime

def run_production_migration():
    """Migration pour la production - Inscription aux lectures"""
    
    print("🚀 MIGRATION PRODUCTION - Inscription aux lectures")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    try:
        # Import des modules Flask
        from app import create_app, db
        from app.models import ReadingParticipation
        
        # Créer l'application
        app = create_app()
        
        with app.app_context():
            print("🔄 Création de la table ReadingParticipation...")
            
            # Créer la nouvelle table
            db.create_all()
            
            # Vérifier que la table a été créée
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'reading_participation' in tables:
                print("✅ Table 'reading_participation' créée avec succès!")
                
                # Afficher la structure
                columns = inspector.get_columns('reading_participation')
                print("\n📊 Structure de la table:")
                for column in columns:
                    print(f"   - {column['name']}: {column['type']}")
                
                print("\n🎉 MIGRATION TERMINÉE AVEC SUCCÈS!")
                print("\n📋 Nouvelles fonctionnalités disponibles:")
                print("   ✅ Inscription aux lectures")
                print("   ✅ Désinscription des lectures")
                print("   ✅ Affichage des participants")
                print("   ✅ Comptage des participants")
                
                return True
            else:
                print("❌ ERREUR: La table n'a pas été créée")
                return False
                
    except ImportError as e:
        print(f"❌ ERREUR D'IMPORT: {e}")
        print("💡 Assurez-vous que l'environnement virtuel est activé")
        return False
    except Exception as e:
        print(f"❌ ERREUR LORS DE LA MIGRATION: {e}")
        return False

def backup_database():
    """Créer une sauvegarde de la base de données avant migration"""
    try:
        import shutil
        
        db_path = "instance/biblioruche.db"
        backup_path = f"instance/biblioruche_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            print(f"✅ Sauvegarde créée: {backup_path}")
            return True
        else:
            print("⚠️  Base de données non trouvée - première installation")
            return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False

if __name__ == "__main__":
    print("🛡️  SAUVEGARDE DE LA BASE DE DONNÉES")
    print("-" * 40)
    
    if not backup_database():
        print("❌ Échec de la sauvegarde - Arrêt de la migration")
        sys.exit(1)
    
    print("\n🔧 DÉBUT DE LA MIGRATION")
    print("-" * 40)
    
    success = run_production_migration()
    
    if success:
        print("\n" + "=" * 60)
        print("🎊 DÉPLOIEMENT RÉUSSI!")
        print("🚀 L'application BiblioRuche est maintenant mise à jour")
        print("📚 Les utilisateurs peuvent s'inscrire aux lectures")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ ÉCHEC DU DÉPLOIEMENT")
        print("🔄 Restaurez la sauvegarde si nécessaire")
        print("📞 Contactez l'équipe technique")
        print("=" * 60)
        sys.exit(1)
