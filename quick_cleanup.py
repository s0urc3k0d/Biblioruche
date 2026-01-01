#!/usr/bin/env python3
"""
Script simple de nettoyage pour BiblioRuche
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import BookProposal, VotingSession, Vote, ReadingSession, User, VoteOption

def quick_cleanup():
    """Nettoyage rapide et simple"""
    app = create_app()
    
    with app.app_context():
        print('🧹 NETTOYAGE SIMPLE DE LA BASE DE DONNÉES')
        print('='*50)
        
        # État initial
        print('\n📊 AVANT:')
        print(f'  Utilisateurs: {User.query.count()}')
        print(f'  Livres: {BookProposal.query.count()}')
        print(f'  Sessions de vote: {VotingSession.query.count()}')
        print(f'  Votes: {Vote.query.count()}')
        print(f'  Lectures: {ReadingSession.query.count()}')
        
        # Supprimer les livres rejetés
        rejected_books = BookProposal.query.filter_by(status='rejected').all()
        print(f'\n📚 Suppression de {len(rejected_books)} livres rejetés...')
        for book in rejected_books:
            db.session.delete(book)
        
        # Supprimer les votes des sessions fermées (garder seulement les actives)
        closed_sessions = VotingSession.query.filter_by(status='closed').all()
        votes_deleted = 0
        sessions_deleted = 0
        
        for session in closed_sessions:
            # Supprimer les votes de cette session
            votes = Vote.query.filter_by(voting_session_id=session.id).all()
            for vote in votes:
                db.session.delete(vote)
                votes_deleted += 1
            
            # Supprimer les options
            options = VoteOption.query.filter_by(voting_session_id=session.id).all()
            for option in options:
                db.session.delete(option)
            
            # Supprimer la session
            db.session.delete(session)
            sessions_deleted += 1
        
        print(f'🗳️  Suppression de {sessions_deleted} sessions fermées et {votes_deleted} votes...')
        
        # Valider
        db.session.commit()
        
        print('\n✅ NETTOYAGE TERMINÉ!')
        
        # État final
        print('\n📊 APRÈS:')
        print(f'  Utilisateurs: {User.query.count()}')
        print(f'  Livres: {BookProposal.query.count()}')
        print(f'  Sessions de vote: {VotingSession.query.count()}')
        print(f'  Votes: {Vote.query.count()}')
        print(f'  Lectures: {ReadingSession.query.count()}')

if __name__ == '__main__':
    quick_cleanup()
