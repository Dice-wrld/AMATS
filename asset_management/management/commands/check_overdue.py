"""
Django management command to check overdue assets
Usage: python manage.py check_overdue
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from asset_management.models import AssetAssignment


class Command(BaseCommand):
    help = 'Check for overdue assets and send notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to consider overdue (default: 30)'
        )

    def handle(self, *args, **options):
        days = options['days']
        threshold = timezone.now() - timedelta(days=days)

        overdue = AssetAssignment.objects.filter(
            date_due__lt=timezone.now(),
            date_returned__isnull=True
        )

        really_overdue = AssetAssignment.objects.filter(
            date_due__lt=threshold,
            date_returned__isnull=True
        )

        self.stdout.write(f'Checking for overdue assets (>{days} days)...')
        self.stdout.write(f'Found {overdue.count()} overdue assignments')
        self.stdout.write(f'Found {really_overdue.count()} critically overdue (>30 days)')

        for assignment in really_overdue[:10]:  # Show first 10
            days_overdue = (timezone.now() - assignment.date_due).days
            self.stdout.write(
                self.style.ERROR(
                    f'OVERDUE: {assignment.asset.asset_tag} - {days_overdue} days - '
                    f'Assigned to: {assignment.assigned_to.get_full_name()}'
                )
            )

        if not overdue.exists():
            self.stdout.write(self.style.SUCCESS('No overdue assets found!'))
