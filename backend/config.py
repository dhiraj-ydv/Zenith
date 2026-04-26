"""
Zenith Configuration — Vault path and application settings.
"""

import os
from pathlib import Path

# Vault settings are now managed dynamically by the VaultManager in services/vault.py

# Backend server
HOST = os.environ.get("ZENITH_HOST", "127.0.0.1")
PORT = int(os.environ.get("ZENITH_PORT", "8000"))

# CORS — allow the Vite dev server (Vite auto-increments ports when busy)
CORS_ORIGINS = [
    f"http://localhost:{port}" for port in range(5173, 5181)
] + [
    f"http://127.0.0.1:{port}" for port in range(5173, 5181)
]
