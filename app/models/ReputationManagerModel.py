# Keep existing classes from reputation manager
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class BlacklistReason(str, Enum):
    MANUAL = "Manual"
    SUSPICIOUS_ACTIVITY = "Suspicious Activity"
    ABUSE = "Abuse"
    SPAM = "Spam"
    MALWARE = "Malware"
    BOTNET = "Botnet"
    SCANNING = "Port Scanning"
    BRUTE_FORCE = "Brute Force Attempts"

class BlacklistEntry(BaseModel):
    ip_address: str
    reason: BlacklistReason
    added_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None

class ReputationScore(BaseModel):
    total_score: int = Field(ge=0)
    attribute_scores: Dict[str, int] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
    factors: List[str] = Field(default_factory=list)

class ReputationRule(BaseModel):
    attribute: str
    points: int = Field(ge=-100, le=100)
    description: Optional[str] = None
    conditions: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)
