#!/usr/bin/env python3
"""
Script de nettoyage de la base de données BiblioRuche
Supprime les données obsolètes et fait du ménage
"""

from app import create_app, db
from app.models import BookProposal, VotingSession, Vote, ReadingSession, User, VoteOption
from datetime import datetime, timedelta

def show_database_stats():
    """Affiche les statistiques de la base de données"""
    print('📊 ÉTAT DE LA BASE DE DONNÉES')
    print('='*50)
    print(f'👥 Utilisateurs: {User.query.count()}')
    print(f'📚 Propositions de livres: {BookProposal.query.count()}')
    print(f'  - Pending: {BookProposal.query.filter_by(status="pending").count()}')
    print(f'  - Approved: {BookProposal.query.filter_by(status="approved").count()}')
    print(f'  - Selected: {BookProposal.query.filter_by(status="selected").count()}')
    print(f'  - Rejected: {BookProposal.query.filter_by(status="rejected").count()}')
    print(f'  - Completed: {BookProposal.query.filter_by(status="completed").count()}')
    print(f'  - Archived: {BookProposal.query.filter_by(status="archived").count()}')
    print(f'🗳️  Sessions de vote: {VotingSession.query.count()}')
    print(f'  - Active: {VotingSession.query.filter_by(status="active").count()}')
    print(f'  - Closed: {VotingSession.query.filter_by(status="closed").count()}')
    print(f'📊 Votes individuels: {Vote.query.count()}')
    print(f'📖 Sessions de lecture: {ReadingSession.query.count()}')
    print(f'  - Current: {ReadingSession.query.filter_by(status="current").count()}')
    print(f'  - Upcoming: {ReadingSession.query.filter_by(status="upcoming").count()}')
    print(f'  - Completed: {ReadingSession.query.filter_by(status="completed").count()}')
    print(f'  - Archived: {ReadingSession.query.filter_by(status="archived").count()}')

def cleanup_old_votes():
    """Supprime les votes de sessions fermées depuis plus de 6 mois"""
    cutoff_date = datetime.now() - timedelta(days=180)
    old_sessions = VotingSession.query.filter(
        VotingSession.status == 'closed',
        VotingSession.end_date < cutoff_date
    ).all()
    
    deleted_votes = 0
    deleted_sessions = 0
    
    for session in old_sessions:
        # Supprimer tous les votes de cette session
        votes = Vote.query.filter_by(voting_session_id=session.id).all()
        for vote in votes:
            db.session.delete(vote)
            deleted_votes += 1
        
        # Supprimer les options de vote
        options = VoteOption.query.filter_by(voting_session_id=session.id).all()
        for option in options:
            db.session.delete(option)
        
        # Supprimer la session
        db.session.delete(session)
        deleted_sessions += 1
    
    return deleted_votes, deleted_sessions

def cleanup_rejected_books():
    """Supprime les livres rejetés depuis plus de 3 mois"""
    cutoff_date = datetime.now() - timedelta(days=90)
    old_rejected = BookProposal.query.filter(
        BookProposal.status == 'rejected',
        BookProposal.created_at < cutoff_date
    ).all()
    
    deleted_books = 0
    for book in old_rejected:
        db.session.delete(book)
        deleted_books += 1
    
    return deleted_books

def cleanup_orphaned_data():
    """Supprime les données orphelines"""
    deleted_votes = 0
    deleted_options = 0
    
    # Supprimer les votes sans session de vote valide
    orphaned_votes = Vote.query.filter(
        ~Vote.voting_session_id.in_(
            db.session.query(VotingSession.id)
        )
    ).all()
    
    for vote in orphaned_votes:
        db.session.delete(vote)
        deleted_votes += 1
    
    # Supprimer les options de vote sans session valide
    orphaned_options = VoteOption.query.filter(
        ~VoteOption.voting_session_id.in_(
            db.session.query(VotingSession.id)
        )
    ).all()
    
    for option in orphaned_options:
        db.session.delete(option)
        deleted_options += 1
    
    return deleted_votes, deleted_options

def main():
    app = create_app()
    
    with app.app_context():
        print('🧹 NETTOYAGE DE LA BASE DE DONNÉES BIBLIORUCHE')
        print('='*60)
        
        # Afficher l'état initial
        print('\n📊 AVANT NETTOYAGE:')
        show_database_stats()
        
        # Demander confirmation
        print('\n❓ Actions de nettoyage disponibles:')
        print('1. Supprimer les votes de sessions fermées depuis +6 mois')
        print('2. Supprimer les livres rejetés depuis +3 mois')
        print('3. Supprimer les données orphelines')
        print('4. Tout nettoyer')
        print('5. Annuler')
        
        choice = input('\n➤ Votre choix (1-5): ').strip()
        
        if choice == '5':
            print('❌ Nettoyage annulé.')
            return
        
        deleted_votes = 0
        deleted_sessions = 0
        deleted_books = 0
        deleted_orphaned_votes = 0
        deleted_orphaned_options = 0
        
        try:
            if choice in ['1', '4']:
                print('\n🗳️  Nettoyage des anciens votes...')
                deleted_votes, deleted_sessions = cleanup_old_votes()
                print(f'   ✅ {deleted_votes} votes supprimés, {deleted_sessions} sessions supprimées')
            
            if choice in ['2', '4']:
                print('\n📚 Nettoyage des livres rejetés...')
                deleted_books = cleanup_rejected_books()
                print(f'   ✅ {deleted_books} livres rejetés supprimés')
            
            if choice in ['3', '4']:
                print('\n🧽 Nettoyage des données orphelines...')
                deleted_orphaned_votes, deleted_orphaned_options = cleanup_orphaned_data()
                print(f'   ✅ {deleted_orphaned_votes} votes orphelins, {deleted_orphaned_options} options orphelines supprimés')
            
            # Valider les changements
            db.session.commit()
            
            print('\n✅ NETTOYAGE TERMINÉ!')
            print(f'📊 Résumé: {deleted_votes + deleted_orphaned_votes} votes, {deleted_sessions} sessions, {deleted_books} livres, {deleted_orphaned_options} options supprimés')
            
            # Afficher l'état final
            print('\n📊 APRÈS NETTOYAGE:')
            show_database_stats()
            
        except Exception as e:
            db.session.rollback()
            print(f'❌ Erreur lors du nettoyage: {e}')

if __name__ == '__main__':
    main()
