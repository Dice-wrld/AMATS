import pytest
from django.contrib.auth.models import User
from asset_management.models import Asset, AssetCategory

@pytest.mark.django_db
def test_asset_creation():
    user = User.objects.create_user(username='tester', password='pass')
    category = AssetCategory.objects.create(name='Laptop')
    asset = Asset.objects.create(
        asset_tag='UTV-LAP-0001',
        name='Test Laptop',
        category=category,
        created_by=user
    )
    assert str(asset).startswith('UTV-LAP-0001')
