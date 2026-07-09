import heapq
from hub import Hub
from connection import Connection


class Pathfinder:
    """Computes optimal paths for all drones using an adapted Dijkstr algorithm"""

    def __init__(self, start_hub: Hub, end_hub: Hub, hubs: list[Hub], connections: list[Connection]) -> None:
        self.start_hub: Hub = start_hub
        self.end_hub: Hub = end_hub
        self.hubs: list[Hub] = hubs
        self.connections: list[Connection] = connections

        # Build an adjacency list representation of the graph for faster lookups
        # Key: hub_name->List of tuples:(neighbor_hub_obj, base_cost_weight)
        self.graph: dict[str, list[tuple[Hub, float]]] = {}
        self._build_graph()

    def _build_graph(self) -> None:
        """Constructs the internal graph structure ignoring blocked zones"""
        # Inicialize dict for all known hubs(including start and end)
        all_hubs = self.hubs + [self.start_hub, self.end_hub]
        for hub in all_hubs:
            if hub.zone != "blocked":
                self.graph[hub.name] = []

        # Populate bidirectional adjacencies based on valid connections
        for conn in self.connections:
            h1, h2 = conn.hub1, conn.hub2
            # Only map links if neither endpoint is blocked
            if h1.name in self.graph and h2.name in self.graph:
                # Cost is determined by the arrival/destination hub zone type
                cost_to_h2 = 2.0 if h2.zone == "restricted" else 1.0
                cost_to_h1 = 2.0 if h1.zone == "restricted" else 1.0
                self.graph[h1.name].append((h2, cost_to_h2))
                self.graph[h2.name].append((h1, cost_to_h1))

    def _dijkstr(self, dynamic_penalties: dict[str, float]) -> list[Hub] | None:
        """Finds a single optimal path from start to end factoring in traffic penalties
        Args:
            dynamic_penalties: dict tracking added weight costs due to congestion
        """
