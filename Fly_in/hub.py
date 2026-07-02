from dataclasses import dataclass


@dataclass
class Hub:
    """Represente a hub in the graph"""

    name: str
    x: int
    y: int
    zone: str = "normal"
    color: str = "none"
    max_drones: int = 1
