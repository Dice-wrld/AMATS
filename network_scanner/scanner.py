"""
Network Scanner - Detects devices on network for asset tracking
Features:
- ARP scanning for MAC address discovery
- Ping sweep for host discovery
- Integration with Django Asset model
"""
import subprocess
import re
import platform
import socket
from typing import List, Dict, Optional
from ipaddress import ip_network


class NetworkScanner:
    """Network scanner to detect devices and match with registered assets"""

    def __init__(self, subnet: str, timeout: int = 1):
        """
        Initialize scanner
        Args:
            subnet: CIDR notation subnet (e.g., '192.168.1.0/24')
            timeout: Timeout in seconds for each host
        """
        self.subnet = subnet
        self.timeout = timeout
        self.results = []

    def scan(self) -> List[Dict]:
        """
        Perform network scan
        Returns:
            List of dictionaries containing scan results
        """
        try:
            network = ip_network(self.subnet, strict=False)
            hosts = list(network.hosts())[:254]  # Limit to first 254 hosts for performance

            results = []
            for host in hosts:
                ip = str(host)
                result = self._scan_host(ip)
                if result:
                    results.append(result)

            return results
        except Exception as e:
            print(f"Scan error: {e}")
            return []

    def _scan_host(self, ip: str) -> Optional[Dict]:
        """Scan individual host"""
        is_alive = self._ping_host(ip)

        if is_alive:
            mac = self._get_mac_address(ip)
            return {
                'ip_address': ip,
                'mac_address': mac,
                'is_alive': True,
                'asset_found': False,
                'asset_id': None,
                'asset_tag': None
            }
        return None

    def _ping_host(self, ip: str) -> bool:
        """Ping host to check if alive"""
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
            timeout_val = str(self.timeout * 1000) if platform.system().lower() == 'windows' else str(self.timeout)
            count = '1'

            result = subprocess.run(
                ['ping', param, count, timeout_param, timeout_val, ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=self.timeout + 2
            )
            return result.returncode == 0
        except:
            return False

    def _get_mac_address(self, ip: str) -> Optional[str]:
        """Get MAC address from ARP table"""
        try:
            system = platform.system().lower()

            if system == 'windows':
                result = subprocess.run(['arp', '-a', ip], capture_output=True, text=True, timeout=5)
                output = result.stdout
                # Parse Windows ARP output
                match = re.search(r'([0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2})', output)
                if match:
                    return match.group(1).replace('-', ':').upper()
            else:
                # Linux/Mac - use ip neigh or arp
                result = subprocess.run(['ip', 'neigh', 'show', ip], capture_output=True, text=True, timeout=5)
                output = result.stdout

                # Parse ip neigh output
                match = re.search(r'lladdr ([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})', output.lower())
                if match:
                    return match.group(1).upper()

                # Fallback to arp command
                result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True, timeout=5)
                output = result.stdout
                match = re.search(r'([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})', output)
                if match:
                    return match.group(1).upper()

        except Exception as e:
            print(f"Error getting MAC for {ip}: {e}")
        return None


def scan_and_update_assets(subnet: str = '192.168.1.0/24') -> Dict:
    """
    Scan network and update asset records
    To be called from Django management command or view
    """
    from asset_management.models import Asset
    from django.utils import timezone

    scanner = NetworkScanner(subnet)
    results = scanner.scan()

    # Match with assets
    matched = 0
    found_missing = 0

    for result in results:
        if result['mac_address']:
            try:
                asset = Asset.objects.get(mac_address__iexact=result['mac_address'])
                asset.network_last_seen = timezone.now()

                # If asset was missing, mark it found
                if asset.status == 'MISSING':
                    asset.status = 'AVAILABLE'
                    asset.location = f"Detected on network: {result['ip_address']}"
                    found_missing += 1

                asset.ip_address = result['ip_address']
                asset.save()

                result['asset_found'] = True
                result['asset_id'] = asset.id
                result['asset_tag'] = asset.asset_tag
                matched += 1

            except Asset.DoesNotExist:
                pass

    return {
        'scanned': len(results),
        'matched': matched,
        'missing_found': found_missing,
        'results': results
    }


if __name__ == '__main__':
    # Test scanner
    import sys
    subnet = sys.argv[1] if len(sys.argv) > 1 else '192.168.1.0/24'
    print(f"Scanning {subnet}...")

    scanner = NetworkScanner(subnet)
    results = scanner.scan()

    print(f"Found {len(results)} devices:")
    for r in results:
        print(f"  {r['ip_address']} - {r['mac_address'] or 'No MAC'}")
