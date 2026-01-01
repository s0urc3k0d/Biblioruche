from flask import Blueprint

print("Création du blueprint...")
auth_bp = Blueprint('auth', __name__)
print(f"Blueprint créé: {auth_bp}")
