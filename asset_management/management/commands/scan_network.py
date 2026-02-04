"""
Django management command to scan network for assets
Usage: python manage.py scan_network --subnet 192.168.1.0/24
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from asset_management.models import Asset
from network_scanner.scanner import NetworkScanner
import sys


class Command(BaseCommand):
    help = 'Scan network for assets and update their status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--subnet',
            type=str,
            default='192.168.1.0/24',
            help='Subnet to scan (default: 192.168.1.0/24)'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=1,
            help='Timeout in seconds for each host (default: 1)'
        )

    def handle(self, *args, **options):
        subnet = options['subnet']
        timeout = options['timeout']

        self.stdout.write(
            self.style.NOTICE(f'Initiating network scan on {subnet}...')
        )
        self.stdout.write(f'Timeout: {timeout}s per host')
        self.stdout.write('-' * 50)

        scanner = NetworkScanner(subnet, timeout)
        results = scanner.scan()

        found_count = 0
        matched_count = 0
        missing_found = 0

        for result in results:
            if not result['mac_address']:
                continue

            try:
                asset = Asset.objects.get(mac_address__iexact=result['mac_address'])
                asset.network_last_seen = timezone.now()
                asset.ip_address = result['ip_address']

                if asset.status == 'MISSING':
                    asset.status = 'AVAILABLE'
                    asset.location = f"Auto-detected: {result['ip_address']}"
                    missing_found += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[FOUND MISSING] {asset.asset_tag} at {result["ip_address"]}'
                        )
                    )
                else:
                    self.stdout.write(
                        f'[DETECTED] {asset.asset_tag} at {result["ip_address"]}'
                    )

                asset.save()
                matched_count += 1

            except Asset.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'[UNKNOWN] Device at {result["ip_address"]} - {result["mac_address"]}'
                    )
                )
                found_count += 1

        self.stdout.write('-' * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f'Scan complete: {len(results)} hosts up, {matched_count} assets matched, {missing_found} missing found'
            )
        )
