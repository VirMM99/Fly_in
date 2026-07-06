from pydantic import BaseModel, field_validator
from hub import Hub


class Connection(BaseModel):
    """Represent a connection between two hubs"""
    hub1: Hub
    hub2: Hub
    max_link_capacity: int = 1

    @field_validator("max_link_capacity")
    @classmethod
    def validate_link_capacity(cls, value: int) -> int:
        """Validate taht max_link_capacity is a positive integer"""
        if value <= 0:
            raise ValueError("max_link_capacity must be a positive integer")
        return value
