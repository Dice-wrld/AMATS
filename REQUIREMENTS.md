# REQUIREMENTS.md

This document traces implementation features back to the field study requirements.

- Authentication & RBAC: Implemented via `UserProfile` with `role` field and Django permissions (maps to requirement 1).
- Asset Management: `Asset`, `AssetCategory`, and `MaintenanceRecord` models cover requirement 2.
- QR Codes: `Asset.generate_qr_code()` generates PNG QR files for labels (requirement 3).
- Issue/Return Workflow: `AssetAssignment` model records transactions and timestamps (requirement 4).
- Network Auto-Update: `network_scanner/scanner.py` (service skeleton) integrates with `Asset.network_last_seen` (requirement 5).
- Audit Trail: `AuditLog` model captures actions (requirement 6).
- Dashboard & Analytics: `dashboard` app skeleton and Chart.js integration (requirement 7).

See `API_DOCS.md` for endpoints and `docs/` for architecture diagrams.
