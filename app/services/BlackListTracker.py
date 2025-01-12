from typing import List, Optional, Set
import ipaddress
from dataclasses import dataclass
from datetime import datetime
import json
import os

@dataclass
class UploadResult:
    success: bool
    total_processed: int
    valid_entries: int
    invalid_entries: int
    error_message: Optional[str] = None

class BlacklistService:
    def __init__(self, storage_path: str = "blacklist_data.json"):
        self.storage_path = storage_path
        self.ip_networks = set()  # Store IP networks (for CIDR)
        self.single_ips = set()   # Store individual IPs
        self.last_upload_time = None
        self._load_from_storage()
    
    def _load_from_storage(self) -> None:
        """Load blacklist data from persistent storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.single_ips = set(data.get('single_ips', []))
                    # Convert stored CIDR strings back to IP network objects
                    self.ip_networks = {ipaddress.ip_network(net) for net in data.get('networks', [])}
                    self.last_upload_time = data.get('last_upload_time')
            except Exception as e:
                print(f"Error loading from storage: {e}")
    
    def _save_to_storage(self) -> None:
        """Save blacklist data to persistent storage."""
        try:
            data = {
                'single_ips': list(self.single_ips),
                'networks': [str(net) for net in self.ip_networks],
                'last_upload_time': self.last_upload_time
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving to storage: {e}")
    
    def _is_valid_cidr(self, entry: str) -> bool:
        """Validate if a string is a valid CIDR notation or IP address."""
        try:
            ipaddress.ip_network(entry.strip(), strict=False)
            return True
        except ValueError:
            return False
    
    def process_entries(self, entries: List[str]) -> UploadResult:
        """Process a list of IP addresses and CIDR ranges."""
        valid_entries = 0
        invalid_entries = 0
        new_networks = set()
        new_single_ips = set()
        
        try:
            for entry in entries:
                entry = entry.strip()
                if self._is_valid_cidr(entry):
                    network = ipaddress.ip_network(entry, strict=False)
                    if network.num_addresses == 1:
                        new_single_ips.add(str(network.network_address))
                    else:
                        new_networks.add(network)
                    valid_entries += 1
                else:
                    invalid_entries += 1
            
            # Update the sets
            self.ip_networks = new_networks
            self.single_ips = new_single_ips
            self.last_upload_time = datetime.now().isoformat()
            
            # Save to persistent storage
            self._save_to_storage()
            
            return UploadResult(
                success=True,
                total_processed=len(entries),
                valid_entries=valid_entries,
                invalid_entries=invalid_entries
            )
            
        except Exception as e:
            return UploadResult(
                success=False,
                total_processed=len(entries),
                valid_entries=valid_entries,
                invalid_entries=invalid_entries,
                error_message=f"Error processing entries: {str(e)}"
            )
    
    def is_ip_blacklisted(self, ip: str) -> bool:
        """Check if an IP address is blacklisted."""
        try:
            ip_addr = ipaddress.ip_address(ip)
            
            # Check if IP is in single IPs list
            if ip in self.single_ips:
                return True
                
            # Check if IP is in any of the networks
            for network in self.ip_networks:
                if ip_addr in network:
                    return True
                    
            return False
        except ValueError:
            raise ValueError("Invalid IP address format")
    
    def get_blacklist_status(self) -> dict:
        """Get current status of the blacklist."""
        return {
            "total_single_ips": len(self.single_ips),
            "total_networks": len(self.ip_networks),
            "last_upload_time": self.last_upload_time,
            "sample_entries": {
                "single_ips": list(self.single_ips)[:5],
                "networks": [str(net) for net in list(self.ip_networks)[:5]]
            }
        }

# Example usage
if __name__ == "__main__":
    service = BlacklistService()
    
    # Example entries including both IPs and CIDR ranges
    entries = [
        "192.168.1.1",
        "10.0.0.0/24",
        "172.16.0.0/16",
        "invalid_ip",
        "8.8.8.8"
    ]
    
    # Process the entries
    result = service.process_entries(entries)
    print(f"Upload result: {result}")
    
    # Check some IPs
    test_ips = ["192.168.1.1", "10.0.0.15", "8.8.8.8", "172.16.0.100"]
    for ip in test_ips:
        is_blocked = service.is_ip_blacklisted(ip)
        print(f"IP {ip} is {'blocked' if is_blocked else 'not blocked'}")
    
    # Get current status
    status = service.get_blacklist_status()
    print(f"Current blacklist status: {status}")