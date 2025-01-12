from typing import Dict, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime
import json
import ipaddress
from pathlib import Path

from app.services.IpGeoLocationTracker import IpGeoLocationTracker

@dataclass
class ReputationScore:
    ip: str
    score: int
    last_updated: str
    location_info: Optional[Dict] = None
    blacklisted: bool = False
    points_breakdown: Optional[Dict[str, int]] = None

class ReputationManager:
    def __init__(
        self,
        blacklist_service,
        point_system,
        storage_path: str = "reputation_data.json"
    ):
        """
        Initialize the Reputation Manager.
        
        Args:
            blacklist_service: BlacklistService instance
            point_system: PointRuleSystem instance
            storage_path: Path to store reputation data
        """
        self.blacklist_service = blacklist_service
        self.point_system = point_system
        self.storage_path = Path(storage_path)
        self.reputation_data: Dict[str, ReputationScore] = {}
        self._load_reputation_data()

    def _load_reputation_data(self) -> None:
        """Load existing reputation data from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for ip, score_data in data.items():
                        self.reputation_data[ip] = ReputationScore(**score_data)
            except Exception as e:
                print(f"Error loading reputation data: {e}")

    def _save_reputation_data(self) -> None:
        """Save reputation data to storage."""
        try:
            data = {
                ip: {
                    'ip': score.ip,
                    'score': score.score,
                    'last_updated': score.last_updated,
                    'location_info': score.location_info,
                    'blacklisted': score.blacklisted,
                    'points_breakdown': score.points_breakdown
                }
                for ip, score in self.reputation_data.items()
            }
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving reputation data: {e}")

    def calculate_reputation(self, ip: str) -> ReputationScore:
        """
        Calculate reputation score for an IP address.
        
        Args:
            ip: IP address to evaluate
            
        Returns:
            ReputationScore: Computed reputation score and metadata
        """
        try:
            # Validate IP address
            ipaddress.ip_address(ip)
            
            # Check blacklist status
            is_blacklisted = self.blacklist_service.is_ip_blacklisted(ip)
            print('is_blacklisted', is_blacklisted)
            # Get geolocation data
            geo_tracker = IpGeoLocationTracker(ip)
            success = geo_tracker.track_ip()
            
            if not success:
                raise ValueError(f"Failed to get geolocation data for IP {ip}")
                
            geo_data = geo_tracker.to_dict()
            
            # Prepare data for point system evaluation
            evaluation_data = {
                "is_eu": geo_data["location"]["is_eu"],
                "country": geo_data["location"]["country"],
                "continent": geo_data["location"]["continent"],
                "latitude": geo_data["location"]["latitude"],
                "longitude": geo_data["location"]["longitude"],
                "connection_type": geo_data["location"]["type"],
                "isp": geo_data["connection"]["isp"],
                "org": geo_data["connection"]["org"],
                "asn": geo_data["connection"]["asn"]
            }
            
            # Calculate points based on rules
            points = self.point_system.evaluate_rules(evaluation_data)
            
            # Create points breakdown
            points_breakdown = {
                "base_points": points,
                "blacklist_penalty": -100 if is_blacklisted else 0,
                "connection_score": 10 if evaluation_data["connection_type"] == "IPv4" else 5,
                "geo_score": 20 if not evaluation_data["is_eu"] else 10  # Example scoring logic
            }
            
            # Calculate final score
            total_score = sum(points_breakdown.values())
            
            # Create reputation score object
            reputation_score = ReputationScore(
                ip=ip,
                score=total_score,
                last_updated=datetime.now().isoformat(),
                location_info=geo_data,
                blacklisted=is_blacklisted,
                points_breakdown=points_breakdown
            )
            
            # Update stored data
            self.reputation_data[ip] = reputation_score
            self._save_reputation_data()
            
            return reputation_score
            
        except Exception as e:
            raise ValueError(f"Error calculating reputation for IP {ip}: {str(e)}")

    def get_reputation(self, ip: str) -> Optional[ReputationScore]:
        """Get stored reputation data for an IP address."""
        return self.reputation_data.get(ip)

    def bulk_update_reputation(self, ips: List[str]) -> Dict[str, ReputationScore]:
        """Update reputation scores for multiple IPs."""
        results = {}
        for ip in ips:
            try:
                score = self.calculate_reputation(ip)
                results[ip] = score                
            except Exception as e:
                print(f"Error updating reputation for IP {ip}: {e}")
        return results

    def get_high_risk_ips(self, threshold: int = 0) -> List[str]:
        """Get list of IPs with scores below threshold."""
        return [
            ip for ip, score in self.reputation_data.items()
            if score.score < threshold or score.blacklisted
        ]

    def get_reputation_stats(self) -> Dict:
        """Get statistical summary of reputation data."""
        if not self.reputation_data:
            return {"total_ips": 0}
            
        scores = [score.score for score in self.reputation_data.values()]
        return {
            "total_ips": len(scores),
            "average_score": sum(scores) / len(scores),
            "blacklisted_count": sum(
                1 for score in self.reputation_data.values() 
                if score.blacklisted
            ),
            "min_score": min(scores),
            "max_score": max(scores)
        }
