"""
Generate reports from command line
Usage: python manage.py generate_report --type inventory --output report.csv
"""
from django.core.management.base import BaseCommand
from asset_management.models import Asset, AssetAssignment
import csv
from datetime import datetime


class Command(BaseCommand):
    help = 'Generate system reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['inventory', 'assignments', 'overdue'],
            default='inventory',
            help='Type of report to generate'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path'
        )

    def handle(self, *args, **options):
        report_type = options['type']
        output = options['output'] or f'{report_type}_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        self.stdout.write(f'Generating {report_type} report...')

        if report_type == 'inventory':
            self.generate_inventory_report(output)
        elif report_type == 'assignments':
            self.generate_assignment_report(output)
        elif report_type == 'overdue':
            self.generate_overdue_report(output)

        self.stdout.write(self.style.SUCCESS(f'Report saved to: {output}'))

    def generate_inventory_report(self, filename):
        assets = Asset.objects.all()
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Asset Tag', 'Name', 'Category', 'Status', 'Condition', 
                           'Location', 'Assigned To', 'Serial Number', 'MAC Address'])
            for asset in assets:
                writer.writerow([
                    asset.asset_tag, asset.name, 
                    asset.category.name if asset.category else '',
                    asset.status, asset.condition, asset.location,
                    asset.assigned_to.username if asset.assigned_to else '',
                    asset.serial_number or '', asset.mac_address or ''
                ])

    def generate_assignment_report(self, filename):
        assignments = AssetAssignment.objects.all()
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Asset', 'Type', 'To User', 'By Admin', 'Date Out', 'Date Due', 'Returned'])
            for a in assignments:
                writer.writerow([
                    a.asset.asset_tag, a.get_assignment_type_display(),
                    a.assigned_to.username, a.assigned_by.username,
                    a.date_out, a.date_due or '', a.date_returned or ''
                ])

    def generate_overdue_report(self, filename):
        from django.utils import timezone
        overdue = AssetAssignment.objects.filter(
            date_due__lt=timezone.now(),
            date_returned__isnull=True
        )
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Asset', 'Assigned To', 'Date Due', 'Days Overdue'])
            for a in overdue:
                days = (timezone.now() - a.date_due).days
                writer.writerow([a.asset.asset_tag, a.assigned_to.username, a.date_due, days])
