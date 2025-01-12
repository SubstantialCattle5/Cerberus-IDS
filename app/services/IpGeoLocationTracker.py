from typing import Optional, Dict
import requests
from requests.exceptions import RequestException
import json
from datetime import datetime
from app.models.IpGeoLocationTrackerModel import TimezoneInfo, ConnectionInfo, LocationInfo
from app.util.ValidateIpAddress import ValidateIpAddress

class IpGeoLocationTracker:
    """
    A class to track IP address information using the IPWHOIS API.
    Uses dataclasses for better data organization and type hints for better code clarity.
    """
    
    API_URL = "http://ipwho.is/{}"
    TIMEOUT = 10  # seconds
    
    def __init__(self, ip: str = "136.233.9.98"):
        """
        Initialize the IP tracker with an IP address.
        
        Args:
            ip (str): The IP address to track
            
        Raises:
            ValueError: If the IP address format is invalid
        """
        if not ValidateIpAddress(ip):
            raise ValueError(f"Invalid IP address format: {ip}")
            
        self.ip = ip
        self.location: Optional[LocationInfo] = None
        self.connection: Optional[ConnectionInfo] = None
        self.timezone: Optional[TimezoneInfo] = None
        

    def track_ip(self) -> bool:
        """
        Fetch and process IP information.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RequestException: If the API request fails
        """
        try:
            response = requests.get(
                self.API_URL.format(self.ip),
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("success", True):  
                raise ValueError(f"API Error: {data.get('message', 'Unknown error')}")
                
            self._process_ip_data(data)
            return True
            
        except RequestException as e:
            raise RequestException(f"Failed to fetch IP data: {str(e)}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse API response: {str(e)}")
            
    def _process_ip_data(self, data: Dict) -> None:
        """Process the API response and populate class attributes."""
        self.location = LocationInfo(
            type=data.get("type", ""),
            continent=data.get("continent", ""),
            continent_code=data.get("continent_code", ""),
            country=data.get("country", ""),
            country_code=data.get("country_code", ""),
            region=data.get("region", ""),
            region_code=data.get("region_code", ""),
            city=data.get("city", ""),
            latitude=float(data.get("latitude", 0)),
            longitude=float(data.get("longitude", 0)),
            is_eu=bool(data.get("is_eu", False)),
            postal=data.get("postal", ""),
            calling_code=data.get("calling_code", ""),
            capital=data.get("capital", ""),
            borders=data.get("borders", []),
            country_flag=data.get("flag", {}).get("emoji", "")
        )
        
        self.connection = ConnectionInfo(
            asn=int(data.get("connection", {}).get("asn", 0)),
            org=data.get("connection", {}).get("org", ""),
            isp=data.get("connection", {}).get("isp", ""),
            domain=data.get("connection", {}).get("domain", "")
        )
        
        timezone_data = data.get("timezone", {})
        self.timezone = TimezoneInfo(
            id=timezone_data.get("id", ""),
            abbr=timezone_data.get("abbr", ""),
            is_dst=bool(timezone_data.get("is_dst", False)),
            offset=int(timezone_data.get("offset", 0)),
            utc=timezone_data.get("utc", ""),
            current_time=datetime.fromisoformat(timezone_data.get("current_time", "").replace("Z", "+00:00"))
        )

    def to_dict(self) -> Dict:
        """Convert the tracker data to a dictionary format."""
        return {
            "ip": self.ip,
            "location": self.location.__dict__ if self.location else None,
            "connection": self.connection.__dict__ if self.connection else None,
            "timezone": self.timezone.__dict__ if self.timezone else None
        }

if __name__ == "__main__":
    try:
        # Example usage
        tracker = IpGeoLocationTracker("8.8.8.8")
        tracker.track_ip()
        
        # Access data through structured objects
        if tracker.location:
            print(f"Location: {tracker.location.city}, {tracker.location.country}")
        
        if tracker.connection:
            print(f"ISP: {tracker.connection.isp}")
        
        if tracker.timezone:
            print(f"Current time: {tracker.timezone.current_time}")
            
        # Get all data as dictionary
        all_data = tracker.to_dict()
        print(json.dumps(all_data, default=str, indent=2))
        
    except (ValueError, RequestException) as e:
        print(f"Error: {e}")