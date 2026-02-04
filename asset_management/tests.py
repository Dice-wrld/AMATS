"""
AMATS Unit Tests
Tests for models, views, and network scanner
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from asset_management.models import Asset, AssetCategory, AssetAssignment, UserProfile, AuditLog


class UserProfileModelTest(TestCase):
    """Test UserProfile model"""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass')

    def test_profile_created_automatically(self):
        """Test that profile is created when user is created"""
        self.assertIsNotNone(self.user.profile)
        self.assertEqual(self.user.profile.role, 'TECH')

    def test_role_methods(self):
        """Test is_admin and is_technician methods"""
        self.assertFalse(self.user.profile.is_admin())
        self.assertTrue(self.user.profile.is_technician())

        self.user.profile.role = 'ADMIN'
        self.user.profile.save()
        self.assertTrue(self.user.profile.is_admin())


class AssetModelTest(TestCase):
    """Test Asset model"""

    def setUp(self):
        self.user = User.objects.create_user('staff', 'staff@test.com', 'pass')
        self.category = AssetCategory.objects.create(name='Test Category')
        self.asset = Asset.objects.create(
            asset_tag='TST-001',
            name='Test Asset',
            category=self.category,
            status='AVAILABLE',
            created_by=self.user,
            mac_address='00:11:22:33:44:55'
        )

    def test_asset_creation(self):
        """Test asset creation"""
        self.assertEqual(str(self.asset), 'TST-001 - Test Asset')
        self.assertEqual(self.asset.status, 'AVAILABLE')

    def test_overdue_detection(self):
        """Test overdue status detection"""
        # Asset not assigned should not be overdue
        self.assertFalse(self.asset.is_overdue())

        # Assign asset with old date
        self.asset.status = 'ASSIGNED'
        self.asset.date_assigned = timezone.now() - timedelta(days=31)
        self.asset.save()

        self.assertTrue(self.asset.is_overdue())


class AssetAssignmentModelTest(TestCase):
    """Test AssetAssignment model"""

    def setUp(self):
        self.admin = User.objects.create_user('admin', 'admin@test.com', 'pass')
        self.tech = User.objects.create_user('tech', 'tech@test.com', 'pass')
        self.category = AssetCategory.objects.create(name='Equipment')
        self.asset = Asset.objects.create(
            asset_tag='EQ-001',
            name='Equipment 1',
            category=self.category,
            status='AVAILABLE',
            created_by=self.admin
        )

    def test_assignment_creation(self):
        """Test creating asset assignment"""
        assignment = AssetAssignment.objects.create(
            asset=self.asset,
            assigned_to=self.tech,
            assigned_by=self.admin,
            assignment_type='ISSUE',
            purpose='Testing'
        )
        self.assertEqual(assignment.assignment_type, 'ISSUE')
        self.assertFalse(assignment.is_overdue())


class LoginViewTest(TestCase):
    """Test login functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        self.user.profile.role = 'TECH'
        self.user.profile.save()

    def test_login_page_loads(self):
        """Test login page renders"""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'asset_management/login.html')

    def test_successful_login(self):
        """Test successful login redirects to dashboard"""
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')


class DashboardAccessTest(TestCase):
    """Test dashboard access control"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('staff', 'staff@test.com', 'pass')

    def test_dashboard_requires_login(self):
        """Test dashboard redirects to login when not authenticated"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_dashboard_accessible_when_logged_in(self):
        """Test dashboard loads when authenticated"""
        self.client.login(username='staff', password='pass')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


class NetworkScannerTest(TestCase):
    """Test network scanner functionality"""

    def test_scanner_initialization(self):
        """Test scanner initializes correctly"""
        from network_scanner.scanner import NetworkScanner
        scanner = NetworkScanner('192.168.1.0/24', timeout=2)
        self.assertEqual(scanner.subnet, '192.168.1.0/24')
        self.assertEqual(scanner.timeout, 2)

    def test_mac_validation(self):
        """Test MAC address validation"""
        from asset_management.forms import AssetForm
        form_data = {
            'asset_tag': 'TST-001',
            'name': 'Test',
            'mac_address': 'invalid-mac'
        }
        form = AssetForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('mac_address', form.errors)


class AuditLogTest(TestCase):
    """Test audit logging"""

    def setUp(self):
        self.user = User.objects.create_user('auditor', 'auditor@test.com', 'pass')

    def test_audit_log_creation(self):
        """Test audit logs are created"""
        log = AuditLog.objects.create(
            user=self.user,
            action='CREATE',
            description='Test action',
            ip_address='192.168.1.1'
        )
        self.assertEqual(log.action, 'CREATE')
        self.assertIsNotNone(log.timestamp)
