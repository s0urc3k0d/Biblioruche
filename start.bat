@echo off
echo Demarrage de BiblioRuche...
echo.

REM Verifier si Python est installe
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou n'est pas dans le PATH
    echo Veuillez installer Python depuis https://python.org
    pause
    exit /b 1
)

REM Verifier si le fichier .env existe
if not exist ".env" (
    echo ERREUR: Le fichier .env n'existe pas
    echo Veuillez copier .env.example vers .env et le configurer
    pause
    exit /b 1
)

REM Installer les dependances si necessaire
echo Installation des dependances...
pip install -r requirements.txt

REM Demarrer l'application
echo.
echo Demarrage de BiblioRuche sur http://localhost:5000
echo Appuyez sur Ctrl+C pour arreter l'application
echo.
python run.py
