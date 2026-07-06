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
        valid = {"normal", "blocked", "restricted", "priority"}
        if value not in valid:
            raise ValueError("Invalid zone")
        return value

    @field_validator("max_drones")
    @classmethod
    def validate_capacity(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("max_drones must be positive")
        return value
