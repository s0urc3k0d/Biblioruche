# -*- coding: utf-8 -*-
"""
Service d'intégration avec l'API Open Library
Permet la recherche et l'auto-complétion des livres
"""

import requests
import logging
from typing import Optional, List, Dict, Any
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
OPEN_LIBRARY_BOOK_URL = "https://openlibrary.org/api/books"
OPEN_LIBRARY_COVERS_URL = "https://covers.openlibrary.org/b"

# Cache timeout en secondes
CACHE_TIMEOUT = 3600  # 1 heure


class OpenLibraryService:
    """Service pour interagir avec l'API Open Library"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BiblioRuche/1.0 (Book Club App)'
        })
        self._cache = {}
        self._cache_times = {}
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache si non expirée"""
        if key in self._cache:
            if time.time() - self._cache_times.get(key, 0) < CACHE_TIMEOUT:
                return self._cache[key]
            else:
                del self._cache[key]
                del self._cache_times[key]
        return None
    
    def _set_cached(self, key: str, value: Any) -> None:
        """Met en cache une valeur"""
        self._cache[key] = value
        self._cache_times[key] = time.time()
    
    def search_books(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recherche des livres par titre ou auteur
        
        Args:
            query: Terme de recherche (titre, auteur, ISBN)
            limit: Nombre maximum de résultats
            
        Returns:
            Liste de dictionnaires avec les informations des livres
        """
        cache_key = f"search:{query}:{limit}"
        cached = self._get_cached(cache_key)
        if cached:
            logger.debug(f"Cache hit for search: {query}")
            return cached
        
        try:
            params = {
                'q': query,
                'limit': limit,
                'fields': 'key,title,author_name,first_publish_year,isbn,cover_i,number_of_pages_median,subject'
            }
            
            response = self.session.get(
                OPEN_LIBRARY_SEARCH_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            books = []
            
            for doc in data.get('docs', []):
                book = {
                    'key': doc.get('key', ''),
                    'title': doc.get('title', 'Titre inconnu'),
                    'authors': doc.get('author_name', ['Auteur inconnu']),
                    'author': ', '.join(doc.get('author_name', ['Auteur inconnu'])),
                    'year': doc.get('first_publish_year'),
                    'isbn': doc.get('isbn', [None])[0] if doc.get('isbn') else None,
                    'cover_id': doc.get('cover_i'),
                    'pages': doc.get('number_of_pages_median'),
                    'subjects': doc.get('subject', [])[:5],  # Limiter à 5 sujets
                }
                
                # Générer l'URL de couverture si disponible
                if book['cover_id']:
                    book['cover_url'] = self.get_cover_url(book['cover_id'], size='M')
                else:
                    book['cover_url'] = None
                
                books.append(book)
            
            self._set_cached(cache_key, books)
            logger.info(f"Found {len(books)} books for query: {query}")
            return books
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout searching for: {query}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching Open Library: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in search: {e}")
            return []
    
    def get_book_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'un livre par son ISBN
        
        Args:
            isbn: Code ISBN (10 ou 13 chiffres)
            
        Returns:
            Dictionnaire avec les informations du livre ou None
        """
        cache_key = f"isbn:{isbn}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # Nettoyer l'ISBN
            clean_isbn = isbn.replace('-', '').replace(' ', '')
            
            params = {
                'bibkeys': f'ISBN:{clean_isbn}',
                'format': 'json',
                'jscmd': 'data'
            }
            
            response = self.session.get(
                OPEN_LIBRARY_BOOK_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            key = f'ISBN:{clean_isbn}'
            
            if key not in data:
                logger.info(f"No book found for ISBN: {isbn}")
                return None
            
            book_data = data[key]
            
            book = {
                'title': book_data.get('title', 'Titre inconnu'),
                'authors': [a.get('name', '') for a in book_data.get('authors', [])],
                'author': ', '.join([a.get('name', '') for a in book_data.get('authors', [])]),
                'publishers': [p.get('name', '') for p in book_data.get('publishers', [])],
                'publish_date': book_data.get('publish_date'),
                'pages': book_data.get('number_of_pages'),
                'isbn': clean_isbn,
                'cover_url': book_data.get('cover', {}).get('medium'),
                'subjects': [s.get('name', '') for s in book_data.get('subjects', [])][:5],
                'url': book_data.get('url'),
            }
            
            self._set_cached(cache_key, book)
            return book
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching book by ISBN {isbn}: {e}")
            return None
    
    def get_cover_url(self, cover_id: int, size: str = 'M') -> str:
        """
        Génère l'URL d'une couverture de livre
        
        Args:
            cover_id: ID de la couverture Open Library
            size: Taille (S=small, M=medium, L=large)
            
        Returns:
            URL de l'image de couverture
        """
        valid_sizes = {'S', 'M', 'L'}
        if size not in valid_sizes:
            size = 'M'
        return f"{OPEN_LIBRARY_COVERS_URL}/id/{cover_id}-{size}.jpg"
    
    def autocomplete(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Auto-complétion rapide pour les champs de formulaire
        
        Args:
            query: Début du titre ou nom d'auteur
            limit: Nombre de suggestions
            
        Returns:
            Liste de suggestions {title, author, year}
        """
        if len(query) < 3:
            return []
        
        books = self.search_books(query, limit=limit)
        
        suggestions = []
        for book in books:
            suggestions.append({
                'title': book['title'],
                'author': book['author'],
                'year': book.get('year', ''),
                'cover_url': book.get('cover_url', ''),
                'display': f"{book['title']} - {book['author']}"
            })
        
        return suggestions


# Instance singleton pour réutilisation
_open_library_service = None


def get_open_library_service() -> OpenLibraryService:
    """Retourne l'instance singleton du service Open Library"""
    global _open_library_service
    if _open_library_service is None:
        _open_library_service = OpenLibraryService()
    return _open_library_service
