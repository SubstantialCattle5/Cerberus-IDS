from fastapi import APIRouter, HTTPException
from typing import Dict, Optional, Union
from app.services.PointRuleBuilder import PointRule, PointRuleSystem

router = APIRouter()

# In-memory storage for the single user's system
system = PointRuleSystem()

# Route to add a new rule to the system
@router.post("/rules", status_code=201)
async def add_rule(rule: PointRule):
    try:
        system.add_rule(rule)
        return {"message": "Rule added successfully", "rule": rule.dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error adding rule: {str(e)}")

# Route to create a new rule group
@router.post("/groups", status_code=201)
async def create_group(name: str, description: Optional[str] = None):
    try:
        group = system.create_group(name=name, description=description)
        return {"message": "Group created successfully", "group": group.dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating group: {str(e)}")

# Route to add a rule to a specific group
@router.post("/groups/{group_name}/rules", status_code=201)
async def add_rule_to_group(group_name: str, rule: PointRule):
    try:
        system.add_to_group(group_name, rule)
        return {"message": "Rule added to group successfully", "rule": rule.dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error adding rule to group: {str(e)}")

# Route to evaluate rules based on input data
@router.post("/evaluate", response_model=dict)
async def evaluate_rules(data: Dict[str, Optional[Union[str, int, float]]]):
    try:
        total_points = system.evaluate_rules(data)
        return {"total_points": total_points}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error evaluating rules: {str(e)}")

# Route to save the rules to a JSON file
@router.post("/save_rules")
async def save_rules(filepath: str):
    try:
        system.save_rules(filepath)
        return {"message": "Rules saved successfully", "filepath": filepath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving rules: {str(e)}")

# Route to load rules from a JSON file
@router.post("/load_rules")
async def load_rules(filepath: str):
    try:
        global system
        system = PointRuleSystem.load_rules(filepath)
        return {"message": "Rules loaded successfully", "system": system.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading rules: {str(e)}")
