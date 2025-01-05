from fastapi import APIRouter, HTTPException
from app.services.ReputationManager import ReputationManager

router = APIRouter()
reputation = ReputationManager()

@router.get("/analyze_ip/{ip_address}", response_model=dict)
async def analyze_ip(ip_address: str):
    try:
        rep = reputation.analyze_ip(ip_address)
        return {"reputation": rep}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error analyzing IP: {str(e)}")