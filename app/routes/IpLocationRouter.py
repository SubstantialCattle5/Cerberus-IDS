from fastapi import APIRouter, HTTPException
from app.services.IpGeoLocationTracker import IpGeoLocationTracker

router = APIRouter()

@router.get("/ip/{ip_address}")
async def ip_location(ip_address: str):
    try:
        tracker = IpGeoLocationTracker(ip_address)
        tracker.track_ip()
        
        # Return the tracker as a dictionary (assuming it has a to_dict method)
        return tracker.to_dict()
    
    except Exception as e:
        # Catch any exceptions and return a 500 Internal Server Error
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
