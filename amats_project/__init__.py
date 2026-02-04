"""amats_project package initializer."""

# Ensure Celery app is loaded when Django starts
try:
	from .celery import app as celery_app  # noqa: F401
except Exception:
	pass

