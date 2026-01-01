#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système d'attribution automatique des badges
"""

from app.models import (
    User, Badge, UserBadge, ReadingParticipation, BookProposal, 
    Vote, BookReview, Film, FilmVote, ViewingParticipation
)
from app import db
from datetime import datetime

class BadgeManager:
    """Gestionnaire des badges automatiques"""
    
    @staticmethod
    def check_and_award_badges(user_id):
        """Vérifier et attribuer tous les badges possibles pour un utilisateur"""
        user = User.query.get(user_id)
        if not user:
            return []
        
        awarded_badges = []
        
        # Vérifier tous les types de badges
        awarded_badges.extend(BadgeManager._check_reading_badges(user))
        awarded_badges.extend(BadgeManager._check_review_badges(user))
        awarded_badges.extend(BadgeManager._check_vote_badges(user))
        awarded_badges.extend(BadgeManager._check_proposal_badges(user))
        awarded_badges.extend(BadgeManager._check_cineclub_badges(user))
        
        return awarded_badges
    
    @staticmethod
    def _award_badge(user, badge_name):
        """Attribuer un badge à un utilisateur si pas déjà possédé"""
        if user.has_badge(badge_name):
            return None
            
        badge = Badge.query.filter_by(name=badge_name).first()
        if not badge:
            return None
        
        user_badge = UserBadge(
            user_id=user.id,
            badge_id=badge.id
        )
        
        db.session.add(user_badge)
        db.session.commit()
        
        return badge
    
    @staticmethod
    def _check_reading_badges(user):
        """Vérifier les badges de lecture"""
        awarded = []
        participation_count = len(user.get_reading_participations())
        
        # Premier pas
        if participation_count >= 1:
            badge = BadgeManager._award_badge(user, "Premier pas")
            if badge:
                awarded.append(badge)
        
        # Lecteur régulier
        if participation_count >= 5:
            badge = BadgeManager._award_badge(user, "Lecteur régulier")
            if badge:
                awarded.append(badge)
        
        # Lecteur assidu
        if participation_count >= 10:
            badge = BadgeManager._award_badge(user, "Lecteur assidu")
            if badge:
                awarded.append(badge)
        
        return awarded
    
    @staticmethod
    def _check_review_badges(user):
        """Vérifier les badges de notation et avis"""
        awarded = []
        review_count = BookReview.query.filter_by(user_id=user.id).count()
        
        # Premier avis
        if review_count >= 1:
            badge = BadgeManager._award_badge(user, "Premier avis")
            if badge:
                awarded.append(badge)
        
        # Critique actif
        if review_count >= 10:
            badge = BadgeManager._award_badge(user, "Critique actif")
            if badge:
                awarded.append(badge)
        
        return awarded
    
    @staticmethod
    def _check_vote_badges(user):
        """Vérifier les badges de vote"""
        awarded = []
        vote_count = len(user.votes)
        
        # Premier vote
        if vote_count >= 1:
            badge = BadgeManager._award_badge(user, "Premier vote")
            if badge:
                awarded.append(badge)
        
        # Voteur actif
        if vote_count >= 5:
            badge = BadgeManager._award_badge(user, "Voteur actif")
            if badge:
                awarded.append(badge)
        
        return awarded
    
    @staticmethod
    def _check_proposal_badges(user):
        """Vérifier les badges de proposition"""
        awarded = []
        proposal_count = len(user.book_proposals)
        accepted_count = len(user.get_accepted_proposals())
        
        # Première proposition
        if proposal_count >= 1:
            badge = BadgeManager._award_badge(user, "Première proposition")
            if badge:
                awarded.append(badge)
        
        # Proposeur
        if accepted_count >= 3:
            badge = BadgeManager._award_badge(user, "Proposeur")
            if badge:
                awarded.append(badge)
        
        # Découvreur
        if accepted_count >= 5:
            badge = BadgeManager._award_badge(user, "Découvreur")
            if badge:
                awarded.append(badge)
        
        return awarded
    
    @staticmethod
    def _check_cineclub_badges(user):
        """Vérifier les badges CinéClub"""
        awarded = []
        
        # Compter les votes films
        film_vote_count = FilmVote.query.filter_by(user_id=user.id).count()
        
        # Compter les participations aux séances
        viewing_count = ViewingParticipation.query.filter_by(user_id=user.id).count()
        
        # Compter les propositions de films
        film_proposal_count = Film.query.filter_by(proposed_by=user.id).count()
        film_approved_count = Film.query.filter_by(
            proposed_by=user.id, 
            status='approved'
        ).count() + Film.query.filter_by(
            proposed_by=user.id,
            status='selected'
        ).count() + Film.query.filter_by(
            proposed_by=user.id,
            status='viewed'
        ).count()
        
        # Premier Film - Première participation à une séance
        if viewing_count >= 1:
            badge = BadgeManager._award_badge(user, "Premier Film")
            if badge:
                awarded.append(badge)
        
        # Cinéphile - 5 séances de visionnage
        if viewing_count >= 5:
            badge = BadgeManager._award_badge(user, "Cinéphile")
            if badge:
                awarded.append(badge)
        
        # Cinéphile passionné - 15 séances de visionnage
        if viewing_count >= 15:
            badge = BadgeManager._award_badge(user, "Cinéphile passionné")
            if badge:
                awarded.append(badge)
        
        # Voteur de films - Premier vote pour un film
        if film_vote_count >= 1:
            badge = BadgeManager._award_badge(user, "Voteur de films")
            if badge:
                awarded.append(badge)
        
        # Critique de cinéma - 10 votes films
        if film_vote_count >= 10:
            badge = BadgeManager._award_badge(user, "Critique de cinéma")
            if badge:
                awarded.append(badge)
        
        # Réalisateur en herbe - Première proposition de film acceptée
        if film_approved_count >= 1:
            badge = BadgeManager._award_badge(user, "Réalisateur en herbe")
            if badge:
                awarded.append(badge)
        
        # Programmateur - 5 propositions de films acceptées
        if film_approved_count >= 5:
            badge = BadgeManager._award_badge(user, "Programmateur")
            if badge:
                awarded.append(badge)
        
        return awarded
    
    @staticmethod
    def award_badges_to_all_users():
        """Attribuer les badges à tous les utilisateurs existants"""
        users = User.query.all()
        total_badges_awarded = 0
        
        print(f"🏆 Attribution des badges pour {len(users)} utilisateurs...")
        
        for user in users:
            awarded = BadgeManager.check_and_award_badges(user.id)
            if awarded:
                badge_names = [badge.name for badge in awarded]
                print(f"   ✅ {user.display_name}: {', '.join(badge_names)}")
                total_badges_awarded += len(awarded)
        
        print(f"\n🎉 {total_badges_awarded} badges attribués au total!")
        return total_badges_awarded
