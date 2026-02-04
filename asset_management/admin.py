"""
AMATS Admin Configuration
"""
from django.contrib import admin
from .models import Asset, AssetCategory, AssetAssignment, UserProfile, AuditLog, MaintenanceRecord


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'department', 'employee_id', 'phone']
    list_filter = ['role', 'department']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'employee_id']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'asset_count', 'created_at']
    search_fields = ['name']

    def asset_count(self, obj):
        return obj.assets.count()


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = [
        'asset_tag', 'name', 'category', 'status', 'condition', 
        'assigned_to', 'location', 'network_last_seen'
    ]
    list_filter = ['status', 'condition', 'category', 'created_at']
    search_fields = ['asset_tag', 'name', 'serial_number', 'mac_address', 'model']
    raw_id_fields = ['assigned_to']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('asset_tag', 'name', 'category', 'description', 'status')
        }),
        ('Technical Specifications', {
            'fields': ('serial_number', 'model', 'manufacturer', 'mac_address', 'ip_address')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'date_assigned', 'location')
        }),
        ('Lifecycle', {
            'fields': ('purchase_date', 'warranty_expiry', 'condition', 'last_maintenance')
        }),
        ('Network Tracking', {
            'fields': ('network_last_seen',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'assigned_to')


@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        'asset', 'assigned_to', 'assigned_by', 'assignment_type', 
        'date_out', 'date_due', 'date_returned', 'is_overdue'
    ]
    list_filter = ['assignment_type', 'date_out', 'date_returned']
    search_fields = ['asset__asset_tag', 'assigned_to__username']
    raw_id_fields = ['asset', 'assigned_to', 'assigned_by']
    date_hierarchy = 'date_out'

    def is_overdue(self, obj):
        return obj.is_overdue()
    is_overdue.boolean = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('asset', 'assigned_to', 'assigned_by')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'model_name', 'description_truncated']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'description', 'model_name']
    date_hierarchy = 'timestamp'
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'description', 'ip_address', 'timestamp']

    def description_truncated(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_truncated.short_description = 'Description'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ['asset', 'maintenance_type', 'date_performed', 'performed_by', 'cost']
    list_filter = ['maintenance_type', 'date_performed']
    search_fields = ['asset__asset_tag', 'description']
    date_hierarchy = 'date_performed'
