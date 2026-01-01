# -*- coding: utf-8 -*-
"""
Routes pour la bibliothèque d'Ebooks
Upload EPUB par admin, téléchargement par utilisateurs connectés
"""

import os
import uuid
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db, limiter
from app.models import Ebook, BookProposal

ebooks_bp = Blueprint('ebooks', __name__, url_prefix='/ebooks')

# =============================================================================
# CONFIGURATION
# =============================================================================

ALLOWED_EBOOK_EXTENSIONS = {'epub'}
ALLOWED_COVER_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_EBOOK_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_COVER_SIZE = 5 * 1024 * 1024   # 5 MB


def allowed_ebook_file(filename):
    """Vérifie si le fichier est un EPUB valide"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EBOOK_EXTENSIONS


def allowed_cover_file(filename):
    """Vérifie si le fichier est une image valide"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_COVER_EXTENSIONS


def validate_epub_content(file_stream):
    """
    Valide le contenu du fichier EPUB (magic bytes)
    Les fichiers EPUB sont des archives ZIP qui commencent par PK
    """
    header = file_stream.read(4)
    file_stream.seek(0)  # Remettre au début
    
    # EPUB/ZIP magic bytes: PK\x03\x04
    if header[:2] != b'PK':
        return False
    
    return True


def get_upload_folder():
    """Retourne le chemin du dossier d'upload des ebooks"""
    upload_folder = os.path.join(current_app.instance_path, 'ebooks')
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder


def get_covers_folder():
    """Retourne le chemin du dossier des couvertures"""
    covers_folder = os.path.join(current_app.instance_path, 'covers')
    os.makedirs(covers_folder, exist_ok=True)
    return covers_folder


def admin_required(f):
    """Décorateur pour les routes admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Accès réservé aux administrateurs.', 'danger')
            return redirect(url_for('ebooks.list_ebooks'))
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# API POUR L'ADMIN
# =============================================================================

@ebooks_bp.route('/api/book/<int:book_id>')
@login_required
@admin_required
def get_book_details(book_id):
    """API pour récupérer les détails d'un livre (pour l'auto-remplissage)"""
    book = BookProposal.query.get_or_404(book_id)
    return {
        'success': True,
        'book': {
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'description': book.description or '',
            'genre': book.genre or '',
            'isbn': book.isbn or '',
            'publication_year': book.publication_year,
            'pages_count': book.pages_count,
            'publisher': book.publisher or '',
            'cover_url': book.cover_url or ''
        }
    }


# =============================================================================
# ROUTES PUBLIQUES
# =============================================================================

@ebooks_bp.route('/')
def list_ebooks():
    """Liste tous les ebooks disponibles"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Filtres
    genre = request.args.get('genre', '')
    search = request.args.get('search', '')
    
    query = Ebook.query.filter_by(is_visible=True)
    
    if genre:
        query = query.filter(Ebook.genre == genre)
    
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Ebook.title.ilike(search_term),
                Ebook.author.ilike(search_term)
            )
        )
    
    ebooks = query.order_by(Ebook.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Récupérer tous les genres uniques pour le filtre
    genres = db.session.query(Ebook.genre).filter(
        Ebook.is_visible == True,
        Ebook.genre.isnot(None)
    ).distinct().order_by(Ebook.genre).all()
    genres = [g[0] for g in genres if g[0]]
    
    return render_template('ebooks/ebooks.html',
                          ebooks=ebooks,
                          genres=genres,
                          current_genre=genre,
                          search=search)


@ebooks_bp.route('/<int:ebook_id>')
def ebook_detail(ebook_id):
    """Affiche les détails d'un ebook"""
    ebook = Ebook.query.get_or_404(ebook_id)
    
    if not ebook.is_visible and (not current_user.is_authenticated or not current_user.is_admin):
        abort(404)
    
    return render_template('ebooks/ebook_detail.html', ebook=ebook)


@ebooks_bp.route('/<int:ebook_id>/download')
@login_required
@limiter.limit("10 per hour")
def download_ebook(ebook_id):
    """Télécharge un ebook (utilisateurs connectés uniquement)"""
    ebook = Ebook.query.get_or_404(ebook_id)
    
    if not ebook.is_visible and not current_user.is_admin:
        abort(404)
    
    filepath = os.path.join(get_upload_folder(), ebook.filename)
    
    if not os.path.exists(filepath):
        flash('Fichier non trouvé.', 'danger')
        return redirect(url_for('ebooks.list_ebooks'))
    
    # Incrémenter le compteur de téléchargements
    ebook.download_count += 1
    db.session.commit()
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=ebook.original_filename
    )


@ebooks_bp.route('/cover/<int:ebook_id>')
def get_cover(ebook_id):
    """Affiche la couverture d'un ebook"""
    ebook = Ebook.query.get_or_404(ebook_id)
    
    if not ebook.cover_filename:
        # Retourner une image par défaut
        return redirect(url_for('static', filename='img/default_cover.png'))
    
    filepath = os.path.join(get_covers_folder(), ebook.cover_filename)
    
    if not os.path.exists(filepath):
        return redirect(url_for('static', filename='img/default_cover.png'))
    
    return send_file(filepath)


# =============================================================================
# ROUTES ADMIN
# =============================================================================

@ebooks_bp.route('/admin')
@login_required
@admin_required
def admin_ebooks():
    """Interface d'administration des ebooks"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    ebooks = Ebook.query.order_by(Ebook.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Stats
    total_ebooks = Ebook.query.count()
    total_downloads = db.session.query(db.func.sum(Ebook.download_count)).scalar() or 0
    
    return render_template('ebooks/admin/manage_ebooks.html',
                          ebooks=ebooks,
                          total_ebooks=total_ebooks,
                          total_downloads=total_downloads)


@ebooks_bp.route('/admin/upload', methods=['GET', 'POST'])
@login_required
@admin_required
def upload_ebook():
    """Upload d'un nouvel ebook"""
    # Récupérer tous les livres disponibles (approuvés, en lecture, terminés, archivés)
    available_books = BookProposal.query.filter(
        BookProposal.status.in_(['approved', 'reading', 'finished', 'archived'])
    ).order_by(BookProposal.title).all()
    
    if request.method == 'POST':
        # Vérifier le fichier EPUB
        if 'epub_file' not in request.files:
            flash('Aucun fichier EPUB sélectionné.', 'danger')
            return redirect(request.url)
        
        epub_file = request.files['epub_file']
        
        if epub_file.filename == '':
            flash('Aucun fichier sélectionné.', 'danger')
            return redirect(request.url)
        
        if not allowed_ebook_file(epub_file.filename):
            flash('Seuls les fichiers EPUB sont autorisés.', 'danger')
            return redirect(request.url)
        
        # Valider le contenu du fichier
        if not validate_epub_content(epub_file.stream):
            flash('Le fichier ne semble pas être un EPUB valide.', 'danger')
            return redirect(request.url)
        
        # Vérifier la taille
        epub_file.seek(0, 2)  # Aller à la fin
        file_size = epub_file.tell()
        epub_file.seek(0)  # Revenir au début
        
        if file_size > MAX_EBOOK_SIZE:
            flash(f'Le fichier est trop volumineux (max {MAX_EBOOK_SIZE // (1024*1024)} MB).', 'danger')
            return redirect(request.url)
        
        # Générer un nom de fichier unique
        original_filename = secure_filename(epub_file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        
        # Sauvegarder le fichier
        filepath = os.path.join(get_upload_folder(), unique_filename)
        epub_file.save(filepath)
        
        # Gérer la couverture (optionnelle)
        cover_filename = None
        if 'cover_file' in request.files:
            cover_file = request.files['cover_file']
            if cover_file.filename != '' and allowed_cover_file(cover_file.filename):
                cover_original = secure_filename(cover_file.filename)
                cover_filename = f"{uuid.uuid4().hex}_{cover_original}"
                cover_path = os.path.join(get_covers_folder(), cover_filename)
                cover_file.save(cover_path)
        
        # Créer l'entrée en base
        ebook = Ebook(
            title=request.form.get('title', '').strip(),
            author=request.form.get('author', '').strip(),
            description=request.form.get('description', '').strip() or None,
            isbn=request.form.get('isbn', '').strip() or None,
            genre=request.form.get('genre', '').strip() or None,
            publication_year=request.form.get('publication_year', type=int) or None,
            pages_count=request.form.get('pages_count', type=int) or None,
            filename=unique_filename,
            original_filename=original_filename,
            file_size=file_size,
            cover_filename=cover_filename,
            uploaded_by=current_user.id,
            is_visible=request.form.get('is_visible') == 'on'
        )
        
        # Liaison avec un livre existant (optionnel)
        book_proposal_id = request.form.get('book_proposal_id', type=int)
        if book_proposal_id:
            ebook.book_proposal_id = book_proposal_id
        
        db.session.add(ebook)
        db.session.commit()
        
        flash(f'Ebook "{ebook.title}" uploadé avec succès !', 'success')
        return redirect(url_for('ebooks.admin_ebooks'))
    
    return render_template('ebooks/admin/upload_ebook.html', available_books=available_books)


@ebooks_bp.route('/admin/edit/<int:ebook_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_ebook(ebook_id):
    """Modifier les informations d'un ebook"""
    ebook = Ebook.query.get_or_404(ebook_id)
    # Récupérer tous les livres disponibles (approuvés, en lecture, terminés, archivés)
    available_books = BookProposal.query.filter(
        BookProposal.status.in_(['approved', 'reading', 'finished', 'archived'])
    ).order_by(BookProposal.title).all()
    
    if request.method == 'POST':
        ebook.title = request.form.get('title', '').strip()
        ebook.author = request.form.get('author', '').strip()
        ebook.description = request.form.get('description', '').strip() or None
        ebook.isbn = request.form.get('isbn', '').strip() or None
        ebook.genre = request.form.get('genre', '').strip() or None
        ebook.publication_year = request.form.get('publication_year', type=int) or None
        ebook.pages_count = request.form.get('pages_count', type=int) or None
        ebook.is_visible = request.form.get('is_visible') == 'on'
        
        # Liaison avec un livre existant
        book_proposal_id = request.form.get('book_proposal_id', type=int)
        ebook.book_proposal_id = book_proposal_id if book_proposal_id else None
        
        # Nouvelle couverture (optionnelle)
        if 'cover_file' in request.files:
            cover_file = request.files['cover_file']
            if cover_file.filename != '' and allowed_cover_file(cover_file.filename):
                # Supprimer l'ancienne couverture
                if ebook.cover_filename:
                    old_cover = os.path.join(get_covers_folder(), ebook.cover_filename)
                    if os.path.exists(old_cover):
                        os.remove(old_cover)
                
                cover_original = secure_filename(cover_file.filename)
                cover_filename = f"{uuid.uuid4().hex}_{cover_original}"
                cover_path = os.path.join(get_covers_folder(), cover_filename)
                cover_file.save(cover_path)
                ebook.cover_filename = cover_filename
        
        db.session.commit()
        flash(f'Ebook "{ebook.title}" modifié avec succès !', 'success')
        return redirect(url_for('ebooks.admin_ebooks'))
    
    return render_template('ebooks/admin/edit_ebook.html', ebook=ebook, available_books=available_books)


@ebooks_bp.route('/admin/delete/<int:ebook_id>', methods=['POST'])
@login_required
@admin_required
def delete_ebook(ebook_id):
    """Supprimer un ebook"""
    ebook = Ebook.query.get_or_404(ebook_id)
    
    # Supprimer les fichiers
    epub_path = os.path.join(get_upload_folder(), ebook.filename)
    if os.path.exists(epub_path):
        os.remove(epub_path)
    
    if ebook.cover_filename:
        cover_path = os.path.join(get_covers_folder(), ebook.cover_filename)
        if os.path.exists(cover_path):
            os.remove(cover_path)
    
    title = ebook.title
    db.session.delete(ebook)
    db.session.commit()
    
    flash(f'Ebook "{title}" supprimé avec succès.', 'success')
    return redirect(url_for('ebooks.admin_ebooks'))


@ebooks_bp.route('/admin/toggle-visibility/<int:ebook_id>', methods=['POST'])
@login_required
@admin_required
def toggle_ebook_visibility(ebook_id):
    """Active/désactive la visibilité d'un ebook"""
    ebook = Ebook.query.get_or_404(ebook_id)
    ebook.is_visible = not ebook.is_visible
    db.session.commit()
    
    status = "visible" if ebook.is_visible else "masqué"
    flash(f'Ebook "{ebook.title}" est maintenant {status}.', 'info')
    return redirect(url_for('ebooks.admin_ebooks'))
