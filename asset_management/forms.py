"""
AMATS Forms - Styled with Django Crispy Forms
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, ButtonHolder
from crispy_forms.bootstrap import FormActions
from .models import Asset, AssetAssignment, AssetCategory, UserProfile, MaintenanceRecord


class LoginForm(AuthenticationForm):
    """Custom login form with crispy styling"""
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            Field('username', css_class='form-control-lg', wrapper_class='mb-3'),
            Field('password', css_class='form-control-lg', wrapper_class='mb-3'),
            FormActions(
                Submit('submit', 'Sign In', css_class='btn btn-primary btn-lg w-100'),
                css_class='d-grid mt-4'
            )
        )


class AssetForm(forms.ModelForm):
    """Form for creating and editing assets"""
    class Meta:
        model = Asset
        fields = [
            'asset_tag', 'name', 'category', 'description', 'serial_number',
            'model', 'manufacturer', 'mac_address', 'purchase_date',
            'warranty_expiry', 'location', 'condition', 'status', 'notes'
        ]
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'warranty_expiry': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'mac_address': forms.TextInput(attrs={'placeholder': '00:1A:2B:3C:4D:5E'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Row(
                Column('asset_tag', css_class='form-group col-md-6 mb-0'),
                Column('name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('category', css_class='form-group col-md-6 mb-0'),
                Column('location', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'description',
            HTML('<hr class="my-3"><h5 class="text-primary">Technical Specifications</h5>'),
            Row(
                Column('serial_number', css_class='form-group col-md-4 mb-0'),
                Column('model', css_class='form-group col-md-4 mb-0'),
                Column('manufacturer', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('mac_address', css_class='form-group col-md-6 mb-0'),
                Column('condition', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            HTML('<hr class="my-3"><h5 class="text-primary">Lifecycle Information</h5>'),
            Row(
                Column('purchase_date', css_class='form-group col-md-6 mb-0'),
                Column('warranty_expiry', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('status', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'notes',
            FormActions(
                Submit('submit', 'Save Asset', css_class='btn btn-primary'),
                HTML('<a href="{% url "asset_list" %}" class="btn btn-secondary ms-2">Cancel</a>')
            )
        )

    def clean_mac_address(self):
        """Validate MAC address format"""
        mac = self.cleaned_data.get('mac_address')
        if mac:
            import re
            if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac):
                raise forms.ValidationError("Invalid MAC address format. Use XX:XX:XX:XX:XX:XX")
        return mac


class AssetIssueForm(forms.ModelForm):
    """Form for issuing assets to technicians"""
    class Meta:
        model = AssetAssignment
        fields = ['assigned_to', 'date_due', 'purpose', 'condition_out', 'notes']
        widgets = {
            'date_due': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'purpose': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Purpose of asset usage...'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users to show only technicians and staff
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
        self.fields['assigned_to'].label = "Assign To"

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('assigned_to', css_class='form-group col-md-6 mb-0'),
                Column('date_due', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'purpose',
            Row(
                Column('condition_out', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'notes',
            FormActions(
                Submit('submit', 'Issue Asset', css_class='btn btn-success'),
                HTML('<a href="{{ request.META.HTTP_REFERER }}" class="btn btn-secondary ms-2">Cancel</a>')
            )
        )


class AssetReturnForm(forms.ModelForm):
    """Form for returning assets"""
    class Meta:
        model = AssetAssignment
        fields = ['condition_returned', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Any issues or observations...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('condition_returned', css_class='form-select-lg'),
            Field('notes', css_class='mt-3'),
            FormActions(
                Submit('submit', 'Confirm Return', css_class='btn btn-warning'),
                HTML('<a href="{% url "dashboard" %}" class="btn btn-secondary ms-2">Cancel</a>')
            )
        )


class AssetFilterForm(forms.Form):
    """Form for filtering assets in list view"""
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search assets...'}))
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + Asset.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=AssetCategory.objects.all(),
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    condition = forms.ChoiceField(
        required=False,
        choices=[('', 'All Conditions')] + Asset.CONDITION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.layout = Layout(
            Row(
                Column('search', css_class='form-group col-md-4 mb-0'),
                Column('status', css_class='form-group col-md-2 mb-0'),
                Column('category', css_class='form-group col-md-3 mb-0'),
                Column('condition', css_class='form-group col-md-3 mb-0'),
                css_class='form-row align-items-end'
            ),
            FormActions(
                Submit('filter', 'Filter', css_class='btn btn-primary btn-sm'),
                HTML('<a href="{% url "asset_list" %}" class="btn btn-outline-secondary btn-sm ms-2">Clear</a>')
            )
        )


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = UserProfile
        fields = ['role', 'department', 'phone', 'employee_id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'email',
            Row(
                Column('role', css_class='form-group col-md-6 mb-0'),
                Column('employee_id', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('department', css_class='form-group col-md-6 mb-0'),
                Column('phone', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Update Profile', css_class='btn btn-primary')
            )
        )

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile.save()
        return profile


class MaintenanceRecordForm(forms.ModelForm):
    """Form for logging maintenance activities"""
    class Meta:
        model = MaintenanceRecord
        fields = ['maintenance_type', 'description', 'date_performed', 'cost', 'next_scheduled']
        widgets = {
            'date_performed': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'next_scheduled': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('maintenance_type', css_class='form-group col-md-6 mb-0'),
                Column('date_performed', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'description',
            Row(
                Column('cost', css_class='form-group col-md-6 mb-0'),
                Column('next_scheduled', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Log Maintenance', css_class='btn btn-primary')
            )
        )


class NetworkScanForm(forms.Form):
    """Form to trigger manual network scan"""
    subnet = forms.CharField(
        max_length=18,
        initial='192.168.1.0/24',
        help_text="Enter subnet to scan (e.g., 192.168.1.0/24)",
        widget=forms.TextInput(attrs={'placeholder': '192.168.1.0/24'})
    )
    timeout = forms.IntegerField(
        initial=1,
        min_value=1,
        max_value=10,
        help_text="Scan timeout per host (seconds)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('subnet', css_class='form-group col-md-8 mb-0'),
                Column('timeout', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('scan', 'Start Network Scan', css_class='btn btn-info'),
                css_class='mt-3'
            )
        )

    def clean_subnet(self):
        import ipaddress
        subnet = self.cleaned_data['subnet']
        try:
            ipaddress.ip_network(subnet, strict=False)
        except ValueError:
            raise forms.ValidationError("Invalid subnet format. Use CIDR notation (e.g., 192.168.1.0/24)")
        return subnet
