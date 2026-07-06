from pydantic import BaseModel, field_validator


class Hub(BaseModel):
    """Represent a hub in the graph"""

    name: str
    x: int
    y: int
    zone: str = "normal"
    color: str = "none"
    max_drones: int = 1

    @field_validator("zone")
    @classmethod
    def validate_zone(cls, value: str) -> str:
        """Validate that the zone type is allowed"""
        valid = {"normal", "blocked", "restricted", "priority"}
        if value not in valid:
            raise ValueError("Invalid zone type: '{value}'")
        return value

    @field_validator("max_drones")
    @classmethod
    def validate_capacity(cls, value: int) -> int:
        """Validate that max_drones capacity is a positive integer"""
        if value <= 0:
            raise ValueError("max_drones capacity must be positive integer")
        return value
