# -*- coding: utf-8 -*-
"""
Service de notifications pour BiblioRuche
Gère l'envoi et la gestion des notifications in-app
"""

import logging
from typing import List, Optional
from app import db
from app.models import Notification, User

logger = logging.getLogger(__name__)


class NotificationService:
    """Service pour gérer les notifications utilisateurs"""
    
    @staticmethod
    def notify_badge_awarded(user_id: int, badge_name: str, badge_description: str) -> Notification:
        """
        Notifie un utilisateur qu'il a reçu un nouveau badge
        
        Args:
            user_id: ID de l'utilisateur
            badge_name: Nom du badge
            badge_description: Description du badge
        """
        return Notification.create_notification(
            user_id=user_id,
            notification_type='badge',
            title=f"🏆 Nouveau badge : {badge_name}",
            message=f"Félicitations ! Vous avez obtenu le badge \"{badge_name}\". {badge_description}",
            link=f"/profile#badges",
            icon='fa-medal'
        )
    
    @staticmethod
    def notify_vote_started(user_id: int, vote_title: str, vote_id: int) -> Notification:
        """Notifie un utilisateur qu'un nouveau vote a commencé"""
        return Notification.create_notification(
            user_id=user_id,
            notification_type='vote',
            title=f"📊 Nouveau vote : {vote_title}",
            message=f"Un nouveau vote est ouvert ! Participez pour choisir le prochain livre à lire.",
            link=f"/vote/{vote_id}",
            icon='fa-check-to-slot'
        )
    
    @staticmethod
    def notify_reading_started(user_id: int, book_title: str, reading_id: int) -> Notification:
        """Notifie un utilisateur qu'une nouvelle lecture commence"""
        return Notification.create_notification(
            user_id=user_id,
            notification_type='reading',
            title=f"📖 Nouvelle lecture : {book_title}",
            message=f"La lecture de \"{book_title}\" commence ! Rejoignez-nous.",
            link=f"/reading/{reading_id}",
            icon='fa-book-open'
        )
    
    @staticmethod
    def notify_book_approved(user_id: int, book_title: str, book_id: int) -> Notification:
        """Notifie un utilisateur que son livre a été approuvé"""
        return Notification.create_notification(
            user_id=user_id,
            notification_type='system',
            title=f"✅ Livre approuvé : {book_title}",
            message=f"Votre proposition \"{book_title}\" a été approuvée par les modérateurs !",
            link=f"/book/{book_id}",
            icon='fa-check-circle'
        )
    
    @staticmethod
    def notify_book_rejected(user_id: int, book_title: str, reason: str = None) -> Notification:
        """Notifie un utilisateur que son livre a été rejeté"""
        message = f"Votre proposition \"{book_title}\" n'a pas été retenue."
        if reason:
            message += f" Raison : {reason}"
        
        return Notification.create_notification(
            user_id=user_id,
            notification_type='system',
            title=f"❌ Livre non retenu : {book_title}",
            message=message,
            icon='fa-times-circle'
        )
    
    @staticmethod
    def notify_viewing_reminder(user_id: int, film_title: str, session_id: int, date_str: str) -> Notification:
        """Rappel de séance de visionnage CinéClub"""
        return Notification.create_notification(
            user_id=user_id,
            notification_type='cineclub',
            title=f"🎬 Rappel : {film_title}",
            message=f"La séance de visionnage de \"{film_title}\" est prévue {date_str}. Ne manquez pas !",
            link=f"/cineclub/viewing/{session_id}",
            icon='fa-film'
        )
    
    @staticmethod
    def notify_new_review(user_id: int, reviewer_name: str, book_title: str, book_id: int) -> Notification:
        """Notifie qu'un nouvel avis a été posté sur un livre"""
        return Notification.create_notification(
            user_id=user_id,
            notification_type='review',
            title=f"💬 Nouvel avis sur {book_title}",
            message=f"{reviewer_name} a laissé un avis sur \"{book_title}\".",
            link=f"/book/{book_id}#reviews",
            icon='fa-star'
        )
    
    @staticmethod
    def broadcast_notification(notification_type: str, title: str, message: str, 
                               link: str = None, exclude_user_ids: List[int] = None) -> int:
        """
        Envoie une notification à tous les utilisateurs
        
        Args:
            notification_type: Type de notification
            title: Titre
            message: Message
            link: Lien optionnel
            exclude_user_ids: Liste d'IDs à exclure
        
        Returns:
            Nombre de notifications envoyées
        """
        users = User.query.all()
        count = 0
        
        for user in users:
            if exclude_user_ids and user.id in exclude_user_ids:
                continue
            
            try:
                Notification.create_notification(
                    user_id=user.id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    link=link
                )
                count += 1
            except Exception as e:
                logger.error(f"Failed to create notification for user {user.id}: {e}")
        
        logger.info(f"Broadcast notification sent to {count} users")
        return count
    
    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        """
        Marque toutes les notifications d'un utilisateur comme lues
        
        Returns:
            Nombre de notifications marquées
        """
        from app.models import utc_now
        
        result = Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).update({
            'is_read': True,
            'read_at': utc_now()
        })
        
        db.session.commit()
        return result
    
    @staticmethod
    def delete_old_notifications(days: int = 30) -> int:
        """
        Supprime les notifications lues de plus de X jours
        
        Args:
            days: Nombre de jours après lesquels supprimer
        
        Returns:
            Nombre de notifications supprimées
        """
        from datetime import timedelta
        from app.models import utc_now
        
        cutoff_date = utc_now() - timedelta(days=days)
        
        result = Notification.query.filter(
            Notification.is_read == True,
            Notification.created_at < cutoff_date
        ).delete()
        
        db.session.commit()
        logger.info(f"Deleted {result} old notifications")
        return result


# Instance singleton
notification_service = NotificationService()
