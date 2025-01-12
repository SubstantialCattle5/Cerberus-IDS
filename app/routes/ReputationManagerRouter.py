from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pathlib import Path

from app.models.ReputationManagerModel import BlacklistReason
from app.services.ReputationManager import ReputationManager 

app = APIRouter()

# Initialize the ReputationManager
current_dir = Path(__file__).parent
rules_file = current_dir / "point_rules.json"
blacklist_file = current_dir / "blacklist.json"
manager = ReputationManager(rules_file=rules_file, blacklist_file=blacklist_file)



# Request models
class AddBlacklistEntryRequest(BaseModel):
    ip_address: str
    reason: str
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None

class AnalyzeIpResponse(BaseModel):
    status: str
    location: Optional[dict] = None
    connection: Optional[dict] = None
    timezone: Optional[dict] = None
    reputation_score: Optional[dict] = None
    blacklist_entry: Optional[dict] = None
    error: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "IP Reputation Manager API is running"}

@app.post("/analyze/{ip_address}", response_model=AnalyzeIpResponse)
def analyze_ip(ip_address: str):
    """Analyze the given IP address."""
    try:
        result = manager.analyze_ip(ip_address)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/blacklist/add")
def add_to_blacklist(request: AddBlacklistEntryRequest):
    """Add an IP address to the blacklist."""
    try:
        manager.add_to_blacklist(
            ip_address=request.ip_address,
            reason=BlacklistReason(reason=request.reason),
            expires_at=request.expires_at,
            notes=request.notes
        )
        return {"message": f"IP {request.ip_address} added to the blacklist"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/blacklist/remove/{ip_address}")
def remove_from_blacklist(ip_address: str):
    """Remove an IP address from the blacklist."""
    try:
        manager.remove_from_blacklist(ip_address)
        return {"message": f"IP {ip_address} removed from the blacklist"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/blacklist/check/{ip_address}")
def check_blacklist(ip_address: str):
    """Check if an IP is blacklisted."""
    try:
        entry = manager.is_blacklisted(ip_address)
        if entry:
            return entry.model_dump()
        return {"message": f"IP {ip_address} is not blacklisted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rules")
def get_rules():
    """Get all reputation rules."""
    try:
        return {"rules": [rule.model_dump() for rule in manager.rules]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rules/save")
def save_rules():
    """Save current rules to the rules file."""
    try:
        manager.save_rules(rules_file)
        return {"message": "Rules saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rules/load")
def load_rules():
    """Load rules from the rules file."""
    try:
        manager.load_rules(rules_file)
        return {"message": "Rules loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/blacklist/save")
def save_blacklist():
    """Save the current blacklist to the blacklist file."""
    try:
        manager.save_blacklist(blacklist_file)
        return {"message": "Blacklist saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/blacklist/load")
def load_blacklist():
    """Load blacklist from the blacklist file."""
    try:
        manager.load_blacklist(blacklist_file)
        return {"message": "Blacklist loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
