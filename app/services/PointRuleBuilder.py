from typing import Dict, List, Optional, Union
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
import json


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


class PointRule(BaseModel):
    """Represents a rule for awarding points based on attribute and value."""
    attribute: GeoAttribute
    value: Optional[Union[str, int, float, bool, List[str]]] = None
    points: int = Field(ge=0, description="Points must be non-negative")
    description: Optional[str] = None

    @field_validator('value')
    def validate_value_for_attribute(cls, v, values):
        print(values)
        """Validate that the value matches the expected type for the attribute."""
        attr = values.data.get("attribute")
        if not attr:
            return v

        if attr in (GeoAttribute.LATITUDE, GeoAttribute.LONGITUDE):
            if not isinstance(v, (int, float)):
                raise ValueError(f"{attr} must be a number")
            if attr == GeoAttribute.LATITUDE and not -90 <= float(v) <= 90:
                raise ValueError("Latitude must be between -90 and 90")
            if attr == GeoAttribute.LONGITUDE and not -180 <= float(v) <= 180:
                raise ValueError("Longitude must be between -180 and 180")
        return v

    def dict(self, *args, **kwargs) -> dict:
        """Convert the model to a dictionary."""
        return {
            "attribute": self.attribute.value,
            "value": self.value,
            "points": self.points,
            "description": self.description
        }


class RuleGroup(BaseModel):
    """Group of related point rules."""
    name: str
    description: Optional[str] = None
    rules: List[PointRule] = Field(default_factory=list)

    def dict(self, *args, **kwargs) -> dict:
        """Convert the model to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "rules": [rule.dict() for rule in self.rules]
        }


class PointRuleSystem(BaseModel):
    """Main system for managing point rules and groups."""
    rules: List[PointRule] = Field(default_factory=list)
    groups: Dict[str, RuleGroup] = Field(default_factory=dict)

    def add_rule(self, rule: PointRule) -> None:
        """Add a single rule to the system."""
        self.rules.append(rule)

    def create_group(self, name: str, description: Optional[str] = None) -> RuleGroup:
        """Create a new rule group."""
        if name in self.groups:
            raise ValueError(f"Group '{name}' already exists")
        group = RuleGroup(name=name, description=description)
        self.groups[name] = group
        return group

    def add_to_group(self, group_name: str, rule: PointRule) -> None:
        """Add a rule to a specific group."""
        if group_name not in self.groups:
            raise ValueError(f"Group '{group_name}' does not exist")
        self.groups[group_name].rules.append(rule)

    def evaluate_rules(self, data: Dict) -> int:
        """Evaluate all rules against provided data and return total points."""
        total_points = 0
        
        # Evaluate individual rules
        for rule in self.rules:
            if rule.attribute.value in data:
                if rule.value is None or data[rule.attribute.value] == rule.value:
                    total_points += rule.points
        
        # Evaluate group rules
        for group in self.groups.values():
            for rule in group.rules:
                if rule.attribute.value in data:
                    if rule.value is None or data[rule.attribute.value] == rule.value:
                        total_points += rule.points
        
        return total_points

    def save_rules(self, filepath: Union[str, Path]) -> None:
        """Save rules and groups to JSON."""
        data = {
            "rules": [rule.dict() for rule in self.rules],
            "groups": {name: group.dict() for name, group in self.groups.items()}
        }
        
        filepath = Path(filepath)
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with filepath.open('w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            raise IOError(f"Failed to save rules: {e}")

    @classmethod
    def load_rules(cls, filepath: Union[str, Path]) -> 'PointRuleSystem':
        """Load rules and groups from JSON."""
        filepath = Path(filepath)
        try:
            with filepath.open('r') as f:
                data = json.load(f)
                
            system = cls()
            
            # Load individual rules
            for rule_data in data.get("rules", []):
                rule_data["attribute"] = GeoAttribute(rule_data["attribute"])
                system.add_rule(PointRule(**rule_data))
            
            # Load groups
            for group_name, group_data in data.get("groups", {}).items():
                group = system.create_group(
                    name=group_name,
                    description=group_data.get("description")
                )
                for rule_data in group_data.get("rules", []):
                    rule_data["attribute"] = GeoAttribute(rule_data["attribute"])
                    group.rules.append(PointRule(**rule_data))
                    
            return system
            
        except Exception as e:
            raise IOError(f"Failed to load rules: {e}")


def example_usage():
    """Example usage of the point rules system."""
    # Create a new system
    system = PointRuleSystem()
    
    # Add individual rules
    system.add_rule(
        PointRule(
            attribute=GeoAttribute.LATITUDE,
            value=45.5,
            points=10,
            description="Northern latitude bonus"
        )
    )
    
    # Create a group for European countries
    eu_group = system.create_group("eu_countries", "European Union Member States")
    
    # Add rules to the group
    system.add_to_group(
        "eu_countries",
        PointRule(
            attribute=GeoAttribute.IS_EU,
            value=True,
            points=20,
            description="EU member state bonus"
        )
    )
    
    # Save the rules
    system.save_rules("point_rules.json")
    
    # Test evaluation
    test_data = {
        "latitude": 45.5,
        "is_eu": True,
        "country": "France"
    }
    
    total_points = system.evaluate_rules(test_data)
    print(f"Total points: {total_points}")
    
    # Load and verify
    loaded_system = PointRuleSystem.load_rules("point_rules.json")
    return loaded_system


if __name__ == "__main__":
    example_usage()