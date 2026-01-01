# -*- coding: utf-8 -*-
"""
Routes API pour BiblioRuche
Endpoints JSON pour les fonctionnalités AJAX
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.services.open_library import get_open_library_service
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/books/search')
def search_books():
    """
    Recherche de livres via Open Library
    
    Query params:
        q: Terme de recherche (requis)
        limit: Nombre max de résultats (défaut: 10)
    
    Returns:
        JSON avec liste de livres
    """
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    if not query or len(query) < 2:
        return jsonify({
            'success': False,
            'error': 'Query too short (minimum 2 characters)',
            'books': []
        })
    
    if limit > 50:
        limit = 50
    
    try:
        service = get_open_library_service()
        books = service.search_books(query, limit=limit)
        
        return jsonify({
            'success': True,
            'query': query,
            'count': len(books),
            'books': books
        })
    except Exception as e:
        logger.error(f"Error in book search API: {e}")
        return jsonify({
            'success': False,
            'error': 'Service temporarily unavailable',
            'books': []
        }), 503


@bp.route('/books/autocomplete')
def autocomplete_books():
    """
    Auto-complétion pour les formulaires de proposition de livre
    
    Query params:
        q: Début du titre/auteur (requis, min 3 caractères)
        limit: Nombre de suggestions (défaut: 5)
    
    Returns:
        JSON avec suggestions
    """
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 5, type=int)
    
    if not query or len(query) < 3:
        return jsonify({
            'suggestions': []
        })
    
    if limit > 20:
        limit = 20
    
    try:
        service = get_open_library_service()
        suggestions = service.autocomplete(query, limit=limit)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        logger.error(f"Error in autocomplete API: {e}")
        return jsonify({
            'success': False,
            'suggestions': []
        }), 503


@bp.route('/books/isbn/<isbn>')
def get_book_by_isbn(isbn):
    """
    Récupère les informations d'un livre par ISBN
    
    Args:
        isbn: Code ISBN (10 ou 13 chiffres)
    
    Returns:
        JSON avec informations du livre
    """
    try:
        service = get_open_library_service()
        book = service.get_book_by_isbn(isbn)
        
        if book:
            return jsonify({
                'success': True,
                'book': book
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Book not found'
            }), 404
    except Exception as e:
        logger.error(f"Error fetching ISBN {isbn}: {e}")
        return jsonify({
            'success': False,
            'error': 'Service temporarily unavailable'
        }), 503


@bp.route('/stats/overview')
def stats_overview():
    """
    Statistiques générales du site
    
    Returns:
        JSON avec statistiques globales
    """
    from app.models import User, BookProposal, ReadingSession, Badge, UserBadge
    from app import db
    
    try:
        stats = {
            'users': {
                'total': User.query.count(),
                'active': User.query.count()  # Tous considérés actifs
            },
            'books': {
                'total': BookProposal.query.count(),
                'approved': BookProposal.query.filter_by(status='approved').count(),
                'pending': BookProposal.query.filter_by(status='pending').count(),
                'completed': BookProposal.query.filter_by(status='completed').count()
            },
            'readings': {
                'total': ReadingSession.query.count(),
                'in_progress': ReadingSession.query.filter_by(status='current').count(),
                'completed': ReadingSession.query.filter_by(status='completed').count()
            },
            'badges': {
                'total': Badge.query.count(),
                'awarded': UserBadge.query.count()
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Could not fetch statistics'
        }), 500


@bp.route('/user/badges')
@login_required
def user_badges():
    """
    Badges de l'utilisateur connecté
    
    Returns:
        JSON avec badges de l'utilisateur
    """
    from app.models import Badge, UserBadge
    
    try:
        user_badges = UserBadge.query.filter_by(user_id=current_user.id).all()
        
        badges = []
        for ub in user_badges:
            badge = Badge.query.get(ub.badge_id)
            if badge:
                badges.append({
                    'id': badge.id,
                    'name': badge.name,
                    'description': badge.description,
                    'icon': badge.icon,
                    'category': badge.category,
                    'color': badge.color,
                    'awarded_at': ub.awarded_at.isoformat() if ub.awarded_at else None
                })
        
        return jsonify({
            'success': True,
            'count': len(badges),
            'badges': badges
        })
    except Exception as e:
        logger.error(f"Error fetching user badges: {e}")
        return jsonify({
            'success': False,
            'error': 'Could not fetch badges'
        }), 500


# =====================================================
# NOTIFICATIONS API
# =====================================================

@bp.route('/notifications')
@login_required
def get_notifications():
    """
    Récupère les notifications de l'utilisateur connecté
    
    Query params:
        limit: Nombre max de notifications (défaut: 20)
        unread_only: Si true, uniquement les non lues
    
    Returns:
        JSON avec liste de notifications
    """
    from app.models import Notification
    
    limit = request.args.get('limit', 20, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    try:
        query = Notification.query.filter_by(user_id=current_user.id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        notifications = query.order_by(
            Notification.is_read.asc(),
            Notification.created_at.desc()
        ).limit(limit).all()
        
        return jsonify({
            'success': True,
            'unread_count': Notification.get_unread_count(current_user.id),
            'notifications': [{
                'id': n.id,
                'type': n.type,
                'title': n.title,
                'message': n.message,
                'link': n.link,
                'icon': n.icon,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat()
            } for n in notifications]
        })
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        return jsonify({
            'success': False,
            'error': 'Could not fetch notifications'
        }), 500


@bp.route('/notifications/count')
@login_required
def get_notification_count():
    """Retourne le nombre de notifications non lues"""
    from app.models import Notification
    
    try:
        count = Notification.get_unread_count(current_user.id)
        return jsonify({
            'success': True,
            'unread_count': count
        })
    except Exception as e:
        logger.error(f"Error fetching notification count: {e}")
        return jsonify({'success': False, 'unread_count': 0}), 500


@bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Marque une notification comme lue"""
    from app.models import Notification
    from app import db
    
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()
        
        if not notification:
            return jsonify({
                'success': False,
                'error': 'Notification not found'
            }), 404
        
        notification.mark_as_read()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notification marked as read'
        })
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return jsonify({'success': False, 'error': 'Failed'}), 500


@bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Marque toutes les notifications comme lues"""
    from app.services.notifications import notification_service
    
    try:
        count = notification_service.mark_all_as_read(current_user.id)
        return jsonify({
            'success': True,
            'marked_count': count
        })
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        return jsonify({'success': False, 'error': 'Failed'}), 500
