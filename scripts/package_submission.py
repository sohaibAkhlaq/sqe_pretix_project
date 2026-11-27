#!/usr/bin/env python3
import os
import zipfile
import argparse
import shutil

# Keep the repository history: it is an explicit course deliverable.
EXCLUDE_DIRS = {
    '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache',
    '.playwright', '.idea', '.vscode', '.scannerwork', 'test-results',
    'playwright-report',
}
EXCLUDE_EXTS = {'.pyc', '.pyo', '.zip'}
EXCLUDE_FILES = {
    '.env', '.coverage', 'final_verify.md',
    'module1.md', 'module2.md', 'module3.md',
    'module4.md', 'module5.md', 'module6.md',
}

def create_zip(zip_filename, pdf_path, root='.'):
    root = os.path.abspath(root)
    zip_filename = os.path.abspath(zip_filename)
    pdf_path = os.path.abspath(pdf_path)
    if os.path.commonpath([root, zip_filename]) != root:
        raise ValueError('Submission ZIP must be written inside the repository root.')
    if os.path.commonpath([root, pdf_path]) != root or not os.path.isfile(pdf_path):
        raise ValueError('The final PDF must exist inside the repository root.')
    if os.path.exists(zip_filename):
        os.remove(zip_filename)
    print(f"Creating archive: {zip_filename}")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as z:
        for current_root, dirs, files in os.walk(root):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                if file in EXCLUDE_FILES or file.endswith('.env.local') or any(file.endswith(ext) for ext in EXCLUDE_EXTS):
                    continue
                if file.lower().endswith('.pdf') and os.path.abspath(os.path.join(current_root, file)) != pdf_path:
                    continue
                file_path = os.path.join(current_root, file)
                rel_path = os.path.relpath(file_path, root)
                z.write(file_path, rel_path)
        names = set(z.namelist())
        if not any(name.startswith('.git/') for name in names):
            raise RuntimeError('Archive does not contain .git history; refusing to label it as a submission.')
        pdfs = [name for name in names if name.lower().endswith('.pdf')]
        if pdfs != [os.path.relpath(pdf_path, root).replace(os.sep, '/')]:
            raise RuntimeError(f'Archive must contain only the selected final PDF, found: {pdfs}')
    print(f"[SUCCESS] {zip_filename} ({os.path.getsize(zip_filename):,} bytes)")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Package one verified project submission archive.')
    parser.add_argument('--output', required=True, help='Required final course filename, including section.')
    parser.add_argument('--pdf', required=True, help='Path to the one final PDF to include.')
    args = parser.parse_args()
    create_zip(args.output, args.pdf)
