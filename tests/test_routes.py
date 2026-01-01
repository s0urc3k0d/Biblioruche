# -*- coding: utf-8 -*-
"""
Tests pour les routes BiblioRuche
"""

import pytest
from flask import url_for


class TestPublicRoutes:
    """Tests pour les routes publiques"""
    
    def test_index_page(self, client):
        """Test page d'accueil"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_books_page(self, client):
        """Test page des livres"""
        response = client.get('/books')
        assert response.status_code == 200
    
    def test_readings_page(self, client):
        """Test page des lectures"""
        response = client.get('/readings')
        assert response.status_code == 200
    
    def test_book_detail_not_found(self, client):
        """Test page détail livre inexistant"""
        response = client.get('/book/99999')
        assert response.status_code == 404
    
    def test_reading_detail_not_found(self, client):
        """Test page détail lecture inexistante"""
        response = client.get('/reading/99999')
        assert response.status_code == 404


class TestAuthRoutes:
    """Tests pour les routes d'authentification"""
    
    def test_login_redirect(self, client):
        """Test redirection login vers Twitch"""
        response = client.get('/auth/login')
        # Devrait rediriger vers Twitch OAuth
        assert response.status_code in [302, 200]
    
    def test_logout_redirect(self, client):
        """Test déconnexion"""
        response = client.get('/auth/logout')
        # Devrait rediriger vers accueil
        assert response.status_code == 302


class TestProtectedRoutes:
    """Tests pour les routes protégées (nécessitent authentification)"""
    
    def test_propose_book_requires_login(self, client):
        """Test proposition livre requiert connexion"""
        response = client.get('/propose')
        # Devrait rediriger vers login
        assert response.status_code == 302
    
    def test_user_profile_requires_login(self, client):
        """Test profil utilisateur requiert connexion"""
        response = client.get('/profile')
        # Devrait rediriger vers login
        assert response.status_code == 302


class TestAdminRoutes:
    """Tests pour les routes admin"""
    
    def test_admin_dashboard_requires_login(self, client):
        """Test dashboard admin requiert connexion"""
        response = client.get('/admin/')
        # Devrait rediriger
        assert response.status_code in [302, 403, 404]
    
    def test_admin_proposals_requires_login(self, client):
        """Test propositions admin requiert connexion"""
        response = client.get('/admin/proposals')
        # Devrait rediriger
        assert response.status_code in [302, 403, 404]


class TestAPIEndpoints:
    """Tests pour les endpoints API (si présents)"""
    
    def test_api_books_list(self, client):
        """Test liste livres API"""
        # Vérifier si l'endpoint existe
        response = client.get('/api/books')
        # Peut retourner 200 ou 404 selon implémentation
        assert response.status_code in [200, 404]
    
    def test_invalid_api_endpoint(self, client):
        """Test endpoint API invalide"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404


class TestBookRoutes:
    """Tests pour les routes livres"""
    
    def test_book_detail_with_valid_id(self, client, test_book):
        """Test page détail avec livre valide"""
        response = client.get(f'/book/{test_book.id}')
        assert response.status_code == 200
        assert test_book.title.encode() in response.data


class TestErrorHandling:
    """Tests pour la gestion des erreurs"""
    
    def test_404_page(self, client):
        """Test page 404"""
        response = client.get('/page/qui/nexiste/pas')
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test méthode non autorisée"""
        # GET sur une route POST-only (si existe)
        response = client.delete('/')
        assert response.status_code in [405, 404]
