from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class TimezoneInfo:
    id: str
    abbr: str
    is_dst: bool
    offset: int
    utc: str
    current_time: datetime

@dataclass
class ConnectionInfo:
    asn: int
    org: str
    isp: str
    domain: str

@dataclass
class LocationInfo:
    type: str
    continent: str
    continent_code: str
    country: str
    country_code: str
    region: str
    region_code: str
    city: str
    latitude: float
    longitude: float
    is_eu: bool
    postal: str
    calling_code: str
    capital: str
    borders: List[str]
    country_flag: str
    
    
