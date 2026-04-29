import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(os.getcwd())

from services.vault import VaultManager
from services.moc import MOCService

vm = VaultManager()
vm.set_active_vault(Path(r"C:\Users\DhirajDesktop11\Documents\test_vault_2"))
moc_service = MOCService(vm)
moc = moc_service.load()

for entry in moc.hierarchy:
    if "fkkkkkkkk" in entry.id:
        print(f"DEBUG: {entry.id} children: {entry.children}")
