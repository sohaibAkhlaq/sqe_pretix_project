"""
Pytest configuration for SQE pretix unit tests.
Supports both isolated execution on host and full-context execution in Docker container.
"""
import os
import sys

# Configure Django settings if pretix is available
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pretix.settings')

try:  # pragma: no cover
    import django
    django.setup()
except Exception:
    # Running outside Django environment with standalone mocks
    pass
