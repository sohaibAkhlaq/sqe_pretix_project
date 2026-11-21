#!/usr/bin/env python3
import os
import zipfile
import shutil

EXCLUDE_DIRS = {'.git', '.venv', 'node_modules', '__pycache__', '.pytest_cache', '.playwright', '.idea', '.vscode'}
EXCLUDE_EXTS = {'.pyc', '.pyo'}
EXCLUDE_FILES = {'Project_24i-3108_24i-3107_24i-3074_A.zip', 'Project_24i-3108_24i-3074_24i-3107.zip'}

def create_zip(zip_filename):
    print(f"Creating archive: {zip_filename}")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk('.'):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                if file in EXCLUDE_FILES or any(file.endswith(ext) for ext in EXCLUDE_EXTS):
                    continue
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, '.')
                z.write(file_path, rel_path)
    print(f"[SUCCESS] {zip_filename} ({os.path.getsize(zip_filename):,} bytes)")

if __name__ == '__main__':
    create_zip('Project_24i-3108_24i-3107_24i-3074_A.zip')
    shutil.copyfile('Project_24i-3108_24i-3107_24i-3074_A.zip', 'Project_24i-3108_24i-3074_24i-3107.zip')
    print("Both submission archives synchronized successfully.")
