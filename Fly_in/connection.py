from pydantic import BaseModel
from hub import Hub


class Connection(BaseModel):
    """Represent a connection between two hubs"""
    hub1: Hub
    hub2: Hub
    max_link_capacity: int = 1
