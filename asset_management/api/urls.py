from rest_framework import routers
from django.urls import path, include
from .views import AssetViewSet, AssetCategoryViewSet, AssetAssignmentViewSet, AuditLogViewSet, MaintenanceRecordViewSet

router = routers.DefaultRouter()
router.register(r'assets', AssetViewSet)
router.register(r'categories', AssetCategoryViewSet)
router.register(r'assignments', AssetAssignmentViewSet)
router.register(r'audit', AuditLogViewSet)
router.register(r'maintenance', MaintenanceRecordViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
