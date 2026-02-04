"""
AMATS App URL Configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Assets
    path('assets/', views.AssetListView.as_view(), name='asset_list'),
    path('assets/create/', views.AssetCreateView.as_view(), name='asset_create'),
    path('assets/<int:pk>/', views.AssetDetailView.as_view(), name='asset_detail'),
    path('assets/<int:pk>/edit/', views.AssetUpdateView.as_view(), name='asset_edit'),
    path('assets/<int:pk>/delete/', views.AssetDeleteView.as_view(), name='asset_delete'),

    # Asset Operations
    path('assets/<int:pk>/issue/', views.issue_asset, name='issue_asset'),
    path('assignments/<int:assignment_id>/return/', views.return_asset, name='return_asset'),

    # Audit and Reports
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit_logs'),
    path('reports/', views.generate_report, name='generate_report'),

    # Network Scanning
    path('network-scan/', views.network_scan_view, name='network_scan'),

    # Profile
    path('profile/', views.profile_view, name='profile'),


    # QR Code features
    path('assets/<int:pk>/qr/', views.generate_asset_qr, name='generate_qr'),
    path('assets/<int:pk>/qr/print/', views.print_asset_qr, name='print_qr'),
    path('qr-scanner/', views.qr_scanner_view, name='qr_scanner'),
    path('qr-lookup/', views.qr_lookup, name='qr_lookup'),

    path('scan-add-asset/', views.scan_add_asset, name='scan_add_asset'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
]
