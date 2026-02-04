# SECURITY.md

This document summarizes how AMATS implements the CIA triad and other security controls.

Confidentiality
- Use environment variables for secrets (`.env`) and never commit them.
- HTTPS/TLS required in production via load balancer (SECURE_SSL_REDIRECT enabled when DEBUG=False).
- Session cookies set with `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` in production.
- Passwords hashed using Django's password hasher (Argon2 recommended in production).
- Database credentials and keys are stored in environment variables or secrets manager.

Integrity
- All actions recorded in `AuditLog` with user, action, timestamp, and IP address.
- Database constraints and unique fields prevent duplicate asset records.
- CSRF protection enabled across forms.
- Content Security Policy (`django-csp`) to mitigate XSS.

Availability
- Dockerized services with health checks.
- Regular backups recommended for production DB.
- Graceful error handlers (custom 404/500 templates).

Operational Security
- Rate limiting for authentication endpoints (`django-ratelimit`).
- Input validation on uploads (file types, sizes) and form validation.
- Immutable append-only audit log design (do not remove logs; mark entries as archived when necessary).

Incident Response
- Monitor `logs/amats.log` and configure external logging/alerting (Sentry, Stackdriver).
- Rotate secrets periodically.

Contact
- Report vulnerabilities to the project maintainer: Amissah Kevin Baiden
