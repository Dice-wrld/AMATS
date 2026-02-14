from rest_framework import serializers
from ..models import Asset, AssetCategory, AssetAssignment, AuditLog, MaintenanceRecord
from django.contrib.auth.models import User
from django.utils import timezone


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetCategory
        fields = ['id', 'name', 'description']


class AssetSerializer(serializers.ModelSerializer):
    category = AssetCategorySerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)

    class Meta:
        model = Asset
        fields = [
            'id', 'asset_tag', 'name', 'category', 'description', 'serial_number',
            'model', 'manufacturer', 'mac_address', 'ip_address', 'status', 'condition',
            'location', 'assigned_to', 'date_assigned', 'network_last_seen', 'qr_code'
        ]


class AssetWriteSerializer(serializers.ModelSerializer):
    """Writable serializer for creating/updating assets via API."""
    category = serializers.PrimaryKeyRelatedField(queryset=AssetCategory.objects.all(), allow_null=True, required=False)
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Asset
        fields = [
            'id', 'asset_tag', 'name', 'category', 'description', 'serial_number',
            'model', 'manufacturer', 'mac_address', 'ip_address', 'status', 'condition',
            'location', 'assigned_to', 'date_assigned', 'purchase_date', 'warranty_expiry',
            'notes'
        ]
        read_only_fields = ['asset_tag']

    def create(self, validated_data):
        assigned = validated_data.pop('assigned_to', None)
        asset = Asset.objects.create(**validated_data)
        if assigned:
            asset.assigned_to = assigned
            asset.status = 'ASSIGNED'
            asset.date_assigned = timezone.now()
            asset.save()
        return asset

    def update(self, instance, validated_data):
        assigned = validated_data.pop('assigned_to', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if assigned is not None:
            instance.assigned_to = assigned
            instance.status = 'ASSIGNED' if assigned else 'AVAILABLE'
            if assigned:
                instance.date_assigned = timezone.now()
            else:
                instance.date_assigned = None
        instance.save()
        return instance


class AssetAssignmentSerializer(serializers.ModelSerializer):
    asset = AssetSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    assigned_by = UserSerializer(read_only=True)

    class Meta:
        model = AssetAssignment
        fields = ['id', 'asset', 'assigned_to', 'assigned_by', 'assignment_type', 'date_out', 'date_due', 'date_returned', 'purpose']


class AssetAssignmentWriteSerializer(serializers.ModelSerializer):
    """Writable serializer for issuing and returning assets via API."""
    class Meta:
        model = AssetAssignment
        fields = ['id', 'asset', 'assigned_to', 'assignment_type', 'date_due', 'purpose']

    def create(self, validated_data):
        request = self.context.get('request')
        assigned_by = request.user if request and request.user.is_authenticated else None
        asset = validated_data.get('asset')

        assignment = AssetAssignment.objects.create(
            asset=asset,
            assigned_to=validated_data.get('assigned_to'),
            assigned_by=assigned_by,
            assignment_type='ISSUE',
            date_due=validated_data.get('date_due'),
            purpose=validated_data.get('purpose', ''),
        )

        # Update asset
        asset.status = 'ASSIGNED'
        asset.assigned_to = assignment.assigned_to
        asset.date_assigned = assignment.date_out
        asset.save()

        # Audit
        AuditLog.objects.create(
            user=assigned_by,
            action='ISSUE',
            model_name='AssetAssignment',
            object_id=str(assignment.id),
            description=f'Issued {asset.asset_tag} to {assignment.assigned_to.username if assignment.assigned_to else "N/A"}'
        )

        return assignment


class AuditLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'model_name', 'object_id', 'description', 'timestamp']


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    asset = AssetSerializer(read_only=True)

    class Meta:
        model = MaintenanceRecord
        fields = ['id', 'asset', 'maintenance_type', 'description', 'performed_by', 'date_performed', 'cost', 'next_scheduled']
