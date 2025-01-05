from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from app.services.IpGeoLocationTracker import IpGeoLocationTracker
from app.models.IpGeoLocationTrackerModel import TimezoneInfo, ConnectionInfo, LocationInfo
from app.models.ReputationManagerModel import BlacklistEntry, BlacklistReason, ReputationScore, ReputationRule
import json

class ReputationManager:
    """IP reputation management system integrated with IpGeoLocationTracker."""
    
    def __init__(
        self,
        rules_file: Optional[Path] = None,
        blacklist_file: Optional[Path] = None,
        cache_duration: int = 3600
    ):
        self.blacklist: Dict[str, BlacklistEntry] = {}
        self.rules: List[ReputationRule] = []
        self.score_cache: Dict[str, ReputationScore] = {}
        self.cache_duration = cache_duration
        self.geo_tracker = None  # Initialize tracker when needed
        
        if rules_file:
            self.load_rules(rules_file)
        if blacklist_file:
            self.load_blacklist(blacklist_file)
    
    def get_geo_data(self, ip_address: str) -> tuple[LocationInfo, ConnectionInfo, TimezoneInfo]:
        """Get geolocation data using IpGeoLocationTracker."""
        if not self.geo_tracker or self.geo_tracker.ip != ip_address:
            self.geo_tracker = IpGeoLocationTracker(ip_address)
            self.geo_tracker.track_ip()
        
        return (
            self.geo_tracker.location,
            self.geo_tracker.connection,
            self.geo_tracker.timezone
        )
    
    
    def analyze_ip(self, ip_address: str) -> dict:
        """Analyze IP address using both geolocation and reputation data."""
        # Check blacklist first
        blacklist_entry = self.is_blacklisted(ip_address)
        if blacklist_entry:
            return {
                "status": "blacklisted",
                "blacklist_entry": blacklist_entry.model_dump(),
                "reputation_score": ReputationScore(
                    total_score=0,
                    factors=["IP is blacklisted"]
                ).model_dump()
            }
        
        try:
            # Get geolocation data
            location, connection, timezone = self.get_geo_data(ip_address)
            
            # Calculate reputation based on the geo data
            reputation = self.calculate_reputation(location, connection)
            
            return {
                "status": "active",
                "location": location.__dict__,
                "connection": connection.__dict__,
                "timezone": timezone.__dict__,
                "reputation_score": reputation.model_dump(),
                "blacklist_entry": None
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def calculate_reputation(self, location: LocationInfo, connection: ConnectionInfo) -> ReputationScore:
        """Calculate reputation score based on location and connection data."""
        total_score = 100  # Base score
        attribute_scores = {}
        factors = []
        
        # Apply location-based rules
        location_dict = location.__dict__
        connection_dict = connection.__dict__
        
        for rule in self.rules:
            # Check location attributes
            if rule.attribute in location_dict:
                value = location_dict[rule.attribute]
                matches_conditions = all(
                    value == condition_value
                    for attr, condition_value in rule.conditions.items()
                )
                
                if matches_conditions:
                    total_score += rule.points
                    attribute_scores[rule.attribute] = rule.points
                    factors.append(rule.description or f"{rule.attribute} match")
            
            # Check connection attributes
            elif rule.attribute in connection_dict:
                value = connection_dict[rule.attribute]
                matches_conditions = all(
                    value == condition_value
                    for attr, condition_value in rule.conditions.items()
                )
                
                if matches_conditions:
                    total_score += rule.points
                    attribute_scores[rule.attribute] = rule.points
                    factors.append(rule.description or f"{rule.attribute} match")
        
        # Apply standard penalties based on connection info
        if connection.domain.endswith(('.proxy', '.vpn', '.tor')):
            penalty = -20
            total_score += penalty
            attribute_scores['proxy_penalty'] = penalty
            factors.append("Proxy/VPN detection penalty")
        
        return ReputationScore(
            total_score=max(0, total_score),
            attribute_scores=attribute_scores,
            factors=factors
        )
    
    def is_blacklisted(self, ip_address: str) -> Optional[BlacklistEntry]:
        """Check if an IP is blacklisted."""
        entry = self.blacklist.get(ip_address)
        if not entry:
            return None
            
        if entry.expires_at and entry.expires_at < datetime.utcnow():
            self.remove_from_blacklist(ip_address)
            return None
            
        return entry
    
    def add_to_blacklist(
        self,
        ip_address: str,
        reason: BlacklistReason,
        expires_at: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> None:
        """Add an IP address to the blacklist."""
        entry = BlacklistEntry(
            ip_address=ip_address,
            reason=reason,
            expires_at=expires_at,
            notes=notes
        )
        self.blacklist[ip_address] = entry
    
    def remove_from_blacklist(self, ip_address: str) -> None:
        """Remove an IP address from the blacklist."""
        self.blacklist.pop(ip_address, None)
    
    def save_rules(self, filepath: Path) -> None:
        """Save reputation rules to file."""
        rules_data = [rule.model_dump() for rule in self.rules]
        filepath.write_text(json.dumps(rules_data, indent=2))
    
    def load_rules(self, filepath: Path) -> None:
        """Load reputation rules from file."""
        if not filepath.exists():
            return
        rules_data = json.loads(filepath.read_text())
        self.rules = [ReputationRule(**rule) for rule in rules_data]
    
    def save_blacklist(self, filepath: Path) -> None:
        """Save blacklist to file."""
        blacklist_data = {
            ip: entry.model_dump() for ip, entry in self.blacklist.items()
        }
        filepath.write_text(json.dumps(blacklist_data, indent=2))
    
    def load_blacklist(self, filepath: Path) -> None:
        """Load blacklist from file."""
        if not filepath.exists():
            return
        blacklist_data = json.loads(filepath.read_text())
        self.blacklist = {
            ip: BlacklistEntry(**entry) for ip, entry in blacklist_data.items()
        }



if __name__ == "__main__":   
    # Initialize the manager
    manager = ReputationManager()
    
    # Add some example rules
    manager.rules.extend([
        ReputationRule(
            attribute="country_code",
            points=10,
            description="Trusted country",
            conditions={"country_code": "US" , "country_code": "CA"}
        ),
        ReputationRule(
            attribute="org",
            points=-20,
            description="Known bad organization",
            conditions={"org": "Suspicious Org Ltd"}
        )
    ])
    
    try:
        # Analyze an IP address
        ip_to_check = "8.8.8.8"
        analysis = manager.analyze_ip(ip_to_check)
        
        print(f"\nAnalysis results for {ip_to_check}:")
        print(f"Status: {analysis['status']}")
        
        if analysis['status'] == "active":
            location = analysis['location']
            connection = analysis['connection']
            print(f"\nLocation: {location['city']}, {location['country']} ({location['country_code']})")
            print(f"ISP: {connection['isp']}")
            print(f"Organization: {connection['org']}")
            
            score = analysis['reputation_score']
            print(f"\nReputation Score: {score['total_score']}")
            print(f"Factors considered: {score['factors']}")
        
        elif analysis['status'] == "blacklisted":
            entry = analysis['blacklist_entry']
            print(f"\nBlacklisted:")
            print(f"Reason: {entry['reason']}")
            print(f"Added: {entry['added_at']}")
            if entry['notes']:
                print(f"Notes: {entry['notes']}")
        
        else:
            print(f"\nError: {analysis['error']}")
    
    except Exception as e:
        print(f"Error during analysis: {e}")