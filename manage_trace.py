#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import warnings
import traceback

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

def custom_warning_handler(message, category, filename, lineno, file=None, line=None):
    traceback.print_stack()
    print(f"WARNING: {message}, Category: {category}, File: {filename}, Line: {lineno}")

warnings.showwarning = custom_warning_handler

if __name__ == '__main__':
    main()
