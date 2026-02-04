from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from ..models import Asset, AssetCategory, AssetAssignment, AuditLog, MaintenanceRecord
from .serializers import AssetSerializer, AssetCategorySerializer, AssetAssignmentSerializer, AuditLogSerializer, MaintenanceRecordSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow superusers and explicit ADMIN role
        if request.user and request.user.is_authenticated and request.user.is_superuser:
            return True
        return request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.is_admin()


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.select_related('category', 'assigned_to').all()
    serializer_class = AssetSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            from .serializers import AssetWriteSerializer
            return AssetWriteSerializer
        return AssetSerializer


class AssetCategoryViewSet(viewsets.ModelViewSet):
    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class AssetAssignmentViewSet(viewsets.ModelViewSet):
    queryset = AssetAssignment.objects.select_related('asset', 'assigned_to', 'assigned_by').all()
    serializer_class = AssetAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create']:
            from .serializers import AssetAssignmentWriteSerializer
            return AssetAssignmentWriteSerializer
        return AssetAssignmentSerializer

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def return_asset(self, request, pk=None):
        """Mark an assignment as returned via API and update asset status."""
        assignment = self.get_object()
        if assignment.date_returned:
            return Response({'detail': 'Assignment already returned.'}, status=400)

        assignment.date_returned = timezone.now()
        assignment.save()

        asset = assignment.asset
        asset.status = 'AVAILABLE'
        asset.assigned_to = None
        asset.date_assigned = None
        asset.save()

        # Audit
        AuditLog.objects.create(
            user=request.user,
            action='RETURN',
            model_name='AssetAssignment',
            object_id=str(assignment.id),
            description=f'Returned {asset.asset_tag} by API'
        )

        serializer = AssetAssignmentSerializer(assignment, context={'request': request})
        return Response(serializer.data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related('user').all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]


class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRecord.objects.select_related('asset').all()
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [IsAdminOrReadOnly]
