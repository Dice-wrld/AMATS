# AMATS API Documentation

## Internal APIs

### Network Scan Endpoint
**Note:** This is used internally by the network scanner module.

### Audit Log Export
Accessible via admin interface or custom management commands.

## Future API Extensions

Planned REST API endpoints for mobile applications:

```
GET  /api/assets/              # List all assets
GET  /api/assets/{id}/         # Asset details
POST /api/assets/{id}/issue/   # Issue asset
POST /api/assets/{id}/return/  # Return asset
GET  /api/user/assignments/    # Current user assignments
POST /api/scan/                # Trigger network scan
```

To be implemented with Django REST Framework.
