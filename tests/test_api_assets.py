import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from asset_management.models import AssetCategory

@pytest.mark.django_db
def test_api_create_asset():
    client = APIClient()
    # create admin user
    admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='pass')
    client.login(username='admin', password='pass')

    category = AssetCategory.objects.create(name='Camera')

    payload = {
        'name': 'Field Camera',
        'category': category.id,
        'serial_number': 'CAM-12345',
        'location': 'Studio 1'
    }

    response = client.post('/api/assets/', payload, format='json')
    assert response.status_code in (200, 201)
    data = response.json()
    assert 'asset_tag' in data or data.get('name') == 'Field Camera'
