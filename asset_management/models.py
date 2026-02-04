"""
AMATS Models - Access Management and Asset Tracking System
UTV Ghana Field Study Implementation
"""
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from django.db import models
import random
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile with role definitions"""
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('TECH', 'Technician'),
        ('SUPERVISOR', 'Supervisor'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='TECH')
    department = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    employee_id = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"
    
    def is_admin(self):
        return self.role == 'ADMIN'
    
    def is_technician(self):
        return self.role == 'TECH'
    
    class Meta:
        permissions = [
            ("can_issue_assets", "Can issue assets to users"),
            ("can_return_assets", "Can process asset returns"),
            ("can_generate_reports", "Can generate system reports"),
        ]


class AssetCategory(models.Model):
    """Categories for IT and Broadcast assets"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Asset Categories"


class Asset(models.Model):
    """IT and Broadcast Equipment Assets"""
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('ASSIGNED', 'Assigned'),
        ('MISSING', 'Missing'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('RETIRED', 'Retired'),
    ]
    
    CONDITION_CHOICES = [
        ('EXCELLENT', 'Excellent'),
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('POOR', 'Poor'),
        ('DAMAGED', 'Damaged'),
    ]
    
    asset_tag = models.CharField(max_length=50, unique=True, help_text="Unique asset identifier (e.g., UTV-LAP-001)")
    name = models.CharField(max_length=200)
    category = models.ForeignKey(AssetCategory, on_delete=models.SET_NULL, null=True, related_name='assets')
    description = models.TextField(blank=True, null=True)
    
    # Technical specifications
    serial_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    mac_address = models.CharField(max_length=17, blank=True, null=True, help_text="MAC Address for network auto-detection")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='GOOD')
    location = models.CharField(max_length=100, default="Main Server Room")
    
    # Assignment tracking
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_assets')
    date_assigned = models.DateTimeField(null=True, blank=True)
    
    # Maintenance and lifecycle
    purchase_date = models.DateField(blank=True, null=True)
    warranty_expiry = models.DateField(blank=True, null=True)
    last_maintenance = models.DateTimeField(blank=True, null=True)
    next_maintenance = models.DateTimeField(blank=True, null=True)
    
    # Security and audit
    network_last_seen = models.DateTimeField(blank=True, null=True, help_text="Last time device was detected on network")
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assets_created')
    
    def __str__(self):
        return f"{self.asset_tag} - {self.name}"

    def _generate_asset_tag(self):
        """Generate a unique asset tag in format UTV-XXX-XXXX"""
        prefix = 'UTV'
        # Use category abbreviation if available
        if self.category and self.category.name:
            cat_abbrev = slugify(self.category.name).upper()[:3]
        else:
            cat_abbrev = 'OTH'

        # Try random 4-digit sequence until unique
        for _ in range(10):
            seq = f"{random.randint(0, 9999):04d}"
            candidate = f"{prefix}-{cat_abbrev}-{seq}"
            if not Asset.objects.filter(asset_tag=candidate).exists():
                return candidate
        # Fallback to UUID short
        return f"{prefix}-{cat_abbrev}-{uuid.uuid4().hex[:6].upper()}"

    def save(self, *args, **kwargs):
        # Ensure asset_tag present
        if not self.asset_tag:
            self.asset_tag = self._generate_asset_tag()

        # Generate QR if missing after create
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating and not self.qr_code:
            try:
                self.generate_qr_code()
                super().save(update_fields=['qr_code'])
            except Exception:
                pass
    
    def is_overdue(self):
        """Check if asset assignment is overdue (configurable threshold)"""
        if self.status == 'ASSIGNED' and self.date_assigned:
            threshold = timezone.now() - timezone.timedelta(days=30)  # 30 days default
            return self.date_assigned < threshold
        return False
    
    def days_since_assignment(self):
        if self.date_assigned:
            return (timezone.now() - self.date_assigned).days
        return None
    
    def generate_qr_code(self):
        """Generate QR code for asset"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # QR code data: asset tag and serial number
        qr_data = f"AMATS|{self.asset_tag}|{self.serial_number or 'N/A'}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to buffer
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f'qr_{self.asset_tag.replace("-", "_")}.png'
        
        # Save to model
        self.qr_code.save(filename, File(buffer), save=False)
        buffer.close()
    
    class Meta:
        ordering = ['-created_at']
        permissions = [
            ("can_view_all_assets", "Can view all assets in system"),
            ("can_edit_assets", "Can edit asset details"),
        ]


class AssetAssignment(models.Model):
    """Track asset issuance and returns"""
    ASSIGNMENT_TYPE = [
        ('ISSUE', 'Issue'),
        ('RETURN', 'Return'),
        ('TRANSFER', 'Transfer'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asset_assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments_approved')
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPE, default='ISSUE')
    
    date_out = models.DateTimeField(auto_now_add=True)
    date_due = models.DateTimeField(blank=True, null=True, help_text="Expected return date")
    date_returned = models.DateTimeField(blank=True, null=True)
    
    condition_out = models.CharField(max_length=20, choices=Asset.CONDITION_CHOICES, default='GOOD')
    condition_returned = models.CharField(max_length=20, choices=Asset.CONDITION_CHOICES, blank=True, null=True)
    
    purpose = models.TextField(help_text="Purpose of asset use")
    notes = models.TextField(blank=True, null=True)
    
    # Security tracking
    acknowledgement_signed = models.BooleanField(default=False, help_text="Physical signature collected")
    checkout_ip = models.GenericIPAddressField(blank=True, null=True)
    return_ip = models.GenericIPAddressField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.asset.asset_tag} -> {self.assigned_to.username} ({self.assignment_type})"
    
    def is_overdue(self):
        if self.date_due and not self.date_returned:
            return timezone.now() > self.date_due
        return False
    
    class Meta:
        ordering = ['-date_out']


class AuditLog(models.Model):
    """System audit trail for compliance"""
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('ISSUE', 'Issue Asset'),
        ('RETURN', 'Return Asset'),
        ('SCAN', 'Network Scan'),
        ('EXPORT', 'Data Export'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, blank=True, null=True)
    object_id = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']


class Notification(models.Model):
    """In-app notification for users (overdue alerts, system messages)."""
    LEVEL_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ALERT', 'Alert'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='INFO')
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Notification to {self.user.username}: {self.message[:40]}"


class MaintenanceRecord(models.Model):
    """Track asset maintenance history"""
    MAINTENANCE_TYPE = [
        ('PREVENTIVE', 'Preventive'),
        ('CORRECTIVE', 'Corrective'),
        ('UPGRADE', 'Upgrade'),
        ('INSPECTION', 'Inspection'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE)
    description = models.TextField()
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_performed = models.DateTimeField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    next_scheduled = models.DateField(blank=True, null=True)
    documents = models.FileField(upload_to='maintenance_docs/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.asset.asset_tag} - {self.maintenance_type} on {self.date_performed}"


# Signal to create user profile automatically
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, employee_id=f"UTV-{instance.id:04d}")

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()