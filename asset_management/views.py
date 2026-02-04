"""
AMATS Views - Access Management and Asset Tracking System
Implements role-based access control and audit logging
"""
import json
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings

from .models import Asset, AssetAssignment, AssetCategory, UserProfile, AuditLog, MaintenanceRecord
from .forms import (
    LoginForm, AssetForm, AssetIssueForm, AssetReturnForm, 
    AssetFilterForm, UserProfileForm, MaintenanceRecordForm, NetworkScanForm
)


# Helper function to create audit logs
def log_audit_action(user, action, description, model_name=None, object_id=None, request=None):
    """Create audit log entry"""
    ip = request.META.get('REMOTE_ADDR') if request else None
    AuditLog.objects.create(
        user=user,
        action=action,
        description=description,
        model_name=model_name,
        object_id=str(object_id) if object_id else None,
        ip_address=ip
    )


def login_view(request):
    """Custom login view with audit logging"""
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            log_audit_action(user, 'LOGIN', f'User {user.username} logged in', request=request)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'asset_management/login.html', {'form': form})


def logout_view(request):
    """Custom logout with audit logging"""
    if request.user.is_authenticated:
        log_audit_action(request.user, 'LOGOUT', f'User {request.user.username} logged out', request=request)
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


class DashboardView(LoginRequiredMixin, View):
    """Main dashboard with statistics and alerts"""
    def get(self, request):
        # Statistics
        total_assets = Asset.objects.count()
        available_assets = Asset.objects.filter(status='AVAILABLE').count()
        assigned_assets = Asset.objects.filter(status='ASSIGNED').count()
        missing_assets = Asset.objects.filter(status='MISSING').count()
        maintenance_assets = Asset.objects.filter(status='MAINTENANCE').count()

        # Recent activities
        recent_assignments = AssetAssignment.objects.select_related('asset', 'assigned_to').all()[:10]
        overdue_assignments = AssetAssignment.objects.filter(
            date_due__lt=timezone.now(), 
            date_returned__isnull=True
        ).select_related('asset', 'assigned_to')

        # Assets needing attention (overdue or missing)
        attention_needed = Asset.objects.filter(
            Q(status='MISSING') | 
            Q(status='ASSIGNED', date_assigned__lt=timezone.now() - timedelta(days=30))
        ).select_related('assigned_to')

        # Category breakdown
        category_stats = AssetCategory.objects.annotate(
            asset_count=Count('assets')
        ).values('name', 'asset_count')

        # Recent audit logs
        recent_logs = AuditLog.objects.select_related('user').all()[:15]

        context = {
            'stats': {
                'total': total_assets,
                'available': available_assets,
                'assigned': assigned_assets,
                'missing': missing_assets,
                'maintenance': maintenance_assets,
            },
            'recent_assignments': recent_assignments,
            'overdue_assignments': overdue_assignments,
            'attention_needed': attention_needed,
            'category_stats': list(category_stats),
            'recent_logs': recent_logs,
            'notifications': [],
            'unread_notifications_count': 0,
        }
        # Fetch unread notifications for user
        try:
            from .models import Notification
            user_notifications = Notification.objects.filter(user=request.user, is_read=False)[:10]
            context['notifications'] = user_notifications
            context['unread_notifications_count'] = user_notifications.count()
        except Exception:
            context['notifications'] = []
            context['unread_notifications_count'] = 0
        return render(request, 'asset_management/dashboard.html', context)


@login_required
def notifications_list(request):
    """Return JSON of unread notifications for current user."""
    from django.http import JsonResponse
    from .models import Notification

    notes = Notification.objects.filter(user=request.user).order_by('-timestamp')[:50]
    data = [
        {
            'id': n.id,
            'message': n.message,
            'link': n.link,
            'level': n.level,
            'is_read': n.is_read,
            'timestamp': n.timestamp.isoformat(),
        }
        for n in notes
    ]
    return JsonResponse({'notifications': data})


@login_required
def mark_notification_read(request, pk):
    """Mark a notification as read."""
    from django.http import JsonResponse
    from .models import Notification

    try:
        note = Notification.objects.get(pk=pk, user=request.user)
        note.is_read = True
        note.save(update_fields=['is_read'])
        return JsonResponse({'status': 'ok'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)


class AssetListView(LoginRequiredMixin, ListView):
    """Asset list with filtering"""
    model = Asset
    template_name = 'asset_management/asset_list.html'
    context_object_name = 'assets'
    paginate_by = 20

    def get_queryset(self):
        queryset = Asset.objects.select_related('category', 'assigned_to').all()

        # Apply filters
        form = AssetFilterForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            status = form.cleaned_data.get('status')
            category = form.cleaned_data.get('category')
            condition = form.cleaned_data.get('condition')

            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) | 
                    Q(asset_tag__icontains=search) |
                    Q(serial_number__icontains=search) |
                    Q(model__icontains=search)
                )
            if status:
                queryset = queryset.filter(status=status)
            if category:
                queryset = queryset.filter(category=category)
            if condition:
                queryset = queryset.filter(condition=condition)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = AssetFilterForm(self.request.GET or None)
        return context


class AssetDetailView(LoginRequiredMixin, DetailView):
    """Detailed asset view with assignment history"""
    model = Asset
    template_name = 'asset_management/asset_detail.html'
    context_object_name = 'asset'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.get_object()
        
        # Get assignment history
        assignments = AssetAssignment.objects.filter(
            asset=asset
        ).select_related('assigned_to', 'assigned_by').order_by('-date_out')
        
        context['assignment_history'] = assignments
        
        # Find active assignment (not returned)
        active_assignment = assignments.filter(date_returned__isnull=True).first()
        context['active_assignment'] = active_assignment
        
        return context


class AssetCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create new asset (Admin only)"""
    model = Asset
    form_class = AssetForm
    template_name = 'asset_management/asset_form.html'
    success_url = reverse_lazy('asset_list')

    def test_func(self):
        return self.request.user.profile.is_admin() or self.request.user.is_superuser

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        log_audit_action(
            self.request.user, 'CREATE', 
            f'Created asset {form.instance.asset_tag}',
            'Asset', form.instance.id,
            self.request
        )
        messages.success(self.request, f'Asset {form.instance.asset_tag} created successfully!')
        return response


class AssetUpdateView(LoginRequiredMixin, UpdateView):
    """Update asset details"""
    model = Asset
    form_class = AssetForm
    template_name = 'asset_management/asset_form.html'
    success_url = reverse_lazy('asset_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit_action(
            self.request.user, 'UPDATE',
            f'Updated asset {form.instance.asset_tag}',
            'Asset', form.instance.id,
            self.request
        )
        messages.success(self.request, f'Asset {form.instance.asset_tag} updated successfully!')
        return response


class AssetDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete asset (Admin only)"""
    model = Asset
    template_name = 'asset_management/asset_confirm_delete.html'
    success_url = reverse_lazy('asset_list')

    def test_func(self):
        return self.request.user.profile.is_admin() or self.request.user.is_superuser

    def delete(self, request, *args, **kwargs):
        asset = self.get_object()
        log_audit_action(
            request.user, 'DELETE',
            f'Deleted asset {asset.asset_tag}',
            'Asset', asset.id,
            request
        )
        messages.success(request, f'Asset {asset.asset_tag} deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def issue_asset(request, pk):
    """Issue asset to technician"""
    asset = get_object_or_404(Asset, pk=pk)

    if asset.status != 'AVAILABLE':
        messages.error(request, 'This asset is not available for issue.')
        return redirect('asset_detail', pk=pk)

    if request.method == 'POST':
        form = AssetIssueForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.asset = asset
            assignment.assigned_by = request.user
            assignment.assignment_type = 'ISSUE'
            assignment.checkout_ip = request.META.get('REMOTE_ADDR')
            assignment.save()

            # Update asset status
            asset.status = 'ASSIGNED'
            asset.assigned_to = assignment.assigned_to
            asset.date_assigned = timezone.now()
            asset.save()

            log_audit_action(
                request.user, 'ISSUE',
                f'Issued {asset.asset_tag} to {assignment.assigned_to.username}',
                'AssetAssignment', assignment.id,
                request
            )

            messages.success(request, f'Asset {asset.asset_tag} issued successfully!')
            return redirect('dashboard')
    else:
        form = AssetIssueForm()

    return render(request, 'asset_management/issue_form.html', {
        'form': form,
        'asset': asset
    })


@login_required
def return_asset(request, assignment_id):
    """Process asset return with error handling"""
    try:
        assignment = AssetAssignment.objects.get(pk=assignment_id, date_returned__isnull=True)
    except AssetAssignment.DoesNotExist:
        messages.error(request, 'No active assignment found for this asset. It may have already been returned.')
        return redirect('asset_list')
    
    asset = assignment.asset
    
    if request.method == 'POST':
        form = AssetReturnForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.date_returned = timezone.now()
            assignment.return_ip = request.META.get('REMOTE_ADDR')
            assignment.save()
            
            # Update asset status
            asset.status = 'AVAILABLE'
            asset.assigned_to = None
            asset.date_assigned = None
            asset.save()
            
            log_audit_action(
                request.user, 'RETURN',
                f'Returned {asset.asset_tag} from {assignment.assigned_to.username}',
                'AssetAssignment', assignment.id,
                request
            )
            
            messages.success(request, f'Asset {asset.asset_tag} returned successfully!')
            return redirect('dashboard')
    else:
        form = AssetReturnForm()
    
    return render(request, 'asset_management/return_form.html', {
        'form': form,
        'assignment': assignment,
        'asset': asset
    })

from django.contrib.auth.models import User

class AuditLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View audit logs (Admin/Supervisor only)"""
    model = AuditLog
    template_name = 'asset_management/audit_log.html'
    context_object_name = 'logs'
    paginate_by = 50

    def test_func(self):
        profile = self.request.user.profile
        return profile.is_admin() or profile.role == 'SUPERVISOR' or self.request.user.is_superuser

    def get_queryset(self):
        queryset = AuditLog.objects.select_related('user').all()

        # Filter by action type if provided
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)

        # Filter by user
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by date range
        days = self.request.GET.get('days', 30)
        if days:
            start_date = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(timestamp__gte=start_date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actions'] = AuditLog.ACTION_CHOICES
        context['users'] = User.objects.filter(is_active=True)
        return context


@login_required
def profile_view(request):
    """User profile management"""
    profile = request.user.profile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    # Get user's current assignments
    current_assignments = AssetAssignment.objects.filter(
        assigned_to=request.user,
        date_returned__isnull=True
    ).select_related('asset')

    # Get assignment history
    assignment_history = AssetAssignment.objects.filter(
        assigned_to=request.user,
        date_returned__isnull=False
    ).select_related('asset').order_by('-date_returned')[:10]

    return render(request, 'asset_management/profile.html', {
        'form': form,
        'current_assignments': current_assignments,
        'assignment_history': assignment_history
    })


@login_required
def network_scan_view(request):
    """Manual network scan interface"""
    if not request.user.profile.is_admin():
        messages.error(request, 'Permission denied. Admin access required.')
        return redirect('dashboard')

    scan_results = None

    if request.method == 'POST':
        form = NetworkScanForm(request.POST)
        if form.is_valid():
            subnet = form.cleaned_data['subnet']
            timeout = form.cleaned_data['timeout']

            # Import scanner module
            from network_scanner.scanner import NetworkScanner

            scanner = NetworkScanner(subnet, timeout)
            scan_results = scanner.scan()

            # Update asset network status
            for result in scan_results:
                if result['mac_address']:
                    try:
                        asset = Asset.objects.get(mac_address__iexact=result['mac_address'])
                        asset.network_last_seen = timezone.now()
                        asset.ip_address = result['ip_address']
                        if asset.status == 'MISSING':
                            asset.status = 'AVAILABLE'
                            messages.warning(request, f'Found missing asset {asset.asset_tag} on network!')
                        asset.save()
                    except Asset.DoesNotExist:
                        pass

            log_audit_action(
                request.user, 'SCAN',
                f'Network scan performed on {subnet}. Found {len(scan_results)} devices.',
                request=request
            )

            messages.success(request, f'Network scan completed. Found {len(scan_results)} devices.')
    else:
        form = NetworkScanForm()

    return render(request, 'asset_management/network_scan.html', {
        'form': form,
        'scan_results': scan_results
    })


@login_required
def generate_report(request):
    """Generate CSV/JSON reports"""
    if request.method == 'POST':
        report_type = request.POST.get('report_type')

        if report_type == 'inventory':
            assets = Asset.objects.all().values(
                'asset_tag', 'name', 'category__name', 'status', 
                'condition', 'assigned_to__username', 'location'
            )
            import csv
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'
            writer = csv.DictWriter(response, fieldnames=assets[0].keys() if assets else [])
            writer.writeheader()
            for asset in assets:
                writer.writerow(asset)

            log_audit_action(request.user, 'EXPORT', 'Generated inventory report', request=request)
            return response

        elif report_type == 'assignments':
            assignments = AssetAssignment.objects.all().values(
                'asset__asset_tag', 'assigned_to__username', 'assigned_by__username',
                'date_out', 'date_returned', 'assignment_type'
            )
            import csv
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="assignments_report.csv"'
            if assignments:
                writer = csv.DictWriter(response, fieldnames=assignments[0].keys())
                writer.writeheader()
                for assignment in assignments:
                    writer.writerow(assignment)
            return response

    return render(request, 'asset_management/reports.html')


def check_overdue_assets():
    """Utility to check and alert on overdue assets (can be run via cron)"""
    from django.core.mail import send_mail

    overdue = AssetAssignment.objects.filter(
        date_due__lt=timezone.now(),
        date_returned__isnull=True
    )

    for assignment in overdue:
        # Send notification (if email configured)
        if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
            send_mail(
                subject=f'Overdue Asset Alert: {assignment.asset.asset_tag}',
                message=f'Asset {assignment.asset.name} ({assignment.asset.asset_tag}) is overdue. '
                        f'Assigned to: {assignment.assigned_to.get_full_name()}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[assignment.assigned_by.email],
                fail_silently=True
            )



@login_required
def generate_asset_qr(request, pk):
    """Generate QR code for asset"""
    asset = get_object_or_404(Asset, pk=pk)
    
    if not asset.qr_code:
        asset.generate_qr_code()
        asset.save()
        messages.success(request, f'QR code generated for {asset.asset_tag}')
    
    return redirect('asset_detail', pk=pk)


@login_required
def print_asset_qr(request, pk):
    """Render a print-friendly QR label for an asset."""
    asset = get_object_or_404(Asset, pk=pk)
    # Ensure QR exists
    if not asset.qr_code:
        try:
            asset.generate_qr_code()
            asset.save()
        except Exception:
            pass

    return render(request, 'asset_management/print_qr.html', {
        'asset': asset
    })


@login_required
def qr_scanner_view(request):
    """QR code scanner interface"""
    return render(request, 'asset_management/qr_scanner.html')


@login_required
def qr_lookup(request):
    """Lookup asset by QR code data"""
    if request.method == 'POST':
        qr_data = request.POST.get('qr_data', '')
        
        # Parse QR data format: AMATS|asset_tag|serial_number
        try:
            parts = qr_data.split('|')
            if len(parts) >= 2:
                asset_tag = parts[1]
                try:
                    asset = Asset.objects.get(asset_tag=asset_tag)
                    return redirect('asset_detail', pk=asset.pk)
                except Asset.DoesNotExist:
                    messages.error(request, f'Asset {asset_tag} not found')
            else:
                messages.error(request, 'Invalid QR code format')
        except Exception as e:
            messages.error(request, 'Error reading QR code')
    
    return redirect('qr_scanner')




@login_required
def scan_add_asset(request):
    """Add new asset by scanning QR code"""
    if request.method == 'POST':
        qr_data = request.POST.get('qr_data', '')
        
        # Parse QR data format: AMATS|asset_tag|serial_number
        try:
            parts = qr_data.split('|')
            if len(parts) >= 2:
                asset_tag = parts[1]
                serial_number = parts[2] if len(parts) > 2 else ''
                
                # Check if asset already exists
                if Asset.objects.filter(asset_tag=asset_tag).exists():
                    messages.warning(request, f'Asset {asset_tag} already exists!')
                    return redirect('asset_detail', pk=Asset.objects.get(asset_tag=asset_tag).pk)
                
                # Create new asset with scanned data
                asset = Asset(
                    asset_tag=asset_tag,
                    name=f'Scanned Asset {asset_tag}',  # Default name
                    serial_number=serial_number if serial_number != 'N/A' else '',
                    status='AVAILABLE',
                    condition='GOOD',
                    created_by=request.user
                )
                asset.save()
                
                # Generate QR code
                asset.generate_qr_code()
                asset.save()
                
                log_audit_action(
                    request.user, 'CREATE',
                    f'Created asset {asset.asset_tag} via QR scan',
                    'Asset', asset.id,
                    request
                )
                
                messages.success(request, f'Asset {asset_tag} created successfully via QR scan!')
                return redirect('asset_edit', pk=asset.pk)  # Go to edit to complete details
                
            else:
                messages.error(request, 'Invalid QR code format')
        except Exception as e:
            messages.error(request, f'Error processing QR code: {str(e)}')
    
    return render(request, 'asset_management/scan_add_asset.html')