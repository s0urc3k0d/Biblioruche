#!/usr/bin/env python3
import sys
import os

print("Starting import test...")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    print("Step 1: Testing basic import...")
    import app
    print("✓ app module imported successfully")
except Exception as e:
    print(f"✗ Failed to import app: {e}")
    sys.exit(1)

try:
    print("Step 2: Testing app.routes...")
    import app.routes
    print("✓ app.routes imported successfully")
except Exception as e:
    print(f"✗ Failed to import app.routes: {e}")
    sys.exit(1)

try:
    print("Step 3: Testing app.routes.auth module...")
    import app.routes.auth
    print("✓ app.routes.auth module imported successfully")
    print(f"Module attributes: {dir(app.routes.auth)}")
except Exception as e:
    print(f"✗ Failed to import app.routes.auth: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("Step 4: Testing auth_bp import...")
    from app.routes.auth import auth_bp
    print(f"✓ auth_bp imported successfully: {auth_bp}")
except Exception as e:
    print(f"✗ Failed to import auth_bp: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("All tests passed!")
