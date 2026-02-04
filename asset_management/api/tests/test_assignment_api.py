import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from asset_management.models import AssetCategory, Asset

@pytest.mark.django_db
def test_issue_and_return_asset_api():
    client = APIClient()
    admin = User.objects.create_superuser(username='admin2', email='a2@example.com', password='pass')
    user = User.objects.create_user(username='tech1', password='pass')
    client.login(username='admin2', password='pass')

    cat = AssetCategory.objects.create(name='Microphone')
    asset = Asset.objects.create(name='Test Mic', category=cat, created_by=admin)

    # Issue via API
    payload = {
        'asset': asset.id,
        'assigned_to': user.id,
        'date_due': None,
        'purpose': 'Field work'
    }
    resp = client.post('/api/assignments/', payload, format='json')
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data['asset'] == asset.id or 'id' in data

    # Return via action
    assignment_id = data.get('id')
    resp2 = client.post(f'/api/assignments/{assignment_id}/return_asset/')
    assert resp2.status_code == 200
    assert Asset.objects.get(id=asset.id).status == 'AVAILABLE'
