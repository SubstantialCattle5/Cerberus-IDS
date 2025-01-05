from enum import Enum


class GeoAttribute(str, Enum):
    """Enumeration of valid geographical attributes."""
    COUNTRY = "country"
    COUNTRY_CODE = "country_code"
    CITY = "city"
    CONTINENT = "continent"
    CONTINENT_CODE = "continent_code"
    REGION = "region"
    REGION_CODE = "region_code"
    LATITUDE = "latitude"
    LONGITUDE = "longitude"
    IS_EU = "is_eu"