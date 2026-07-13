from hub import Hub
from connection import Connection


class Pathfinder:
    """Computes optimal paths for all drones
        using an adapted Dijkstr algorithm"""

    def __init__(
                self,
                start_hub: Hub, end_hub: Hub,
                hubs: list[Hub], connections: list[Connection]
            ) -> None:
        self.start_hub: Hub = start_hub
        self.end_hub: Hub = end_hub
        self.hubs: list[Hub] = hubs
        self.connections: list[Connection] = connections
        # Build an adjacency list representation
        # of the graph for faster lookups
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
                # We assigned lower weight to the priority zones(0.5)
                # so the algorithm actively prefers
                # them over the normal ones(1.0)
                # Cost is determined by the arrival/destination hub zone type
                if h2.zone == "restricted":
                    cost_to_h2 = 2.0
                elif h2.zone == "priority":
                    cost_to_h2 = 0.5
                else:
                    cost_to_h2 = 1.0

                if h1.zone == "restricted":
                    cost_to_h1 = 2.0
                elif h1.zone == "priority":
                    cost_to_h1 = 0.5
                else:
                    cost_to_h1 = 1.0

                self.graph[h1.name].append((h2, cost_to_h2))
                self.graph[h2.name].append((h1, cost_to_h1))

    def _dijkstr(
            self,
            dynamic_penalties: dict[str, float]
            ) -> list[Hub] | None:
        """Finds a single optimal path from start to
        end factoring in traffic penalties
        Args:
            dynamic_penalties: dict tracking added weight
            costs due to congestion
        """
        # Dict to track the minimum cost seen to reach each hub
        shortest_costs: dict[str, float] = {self.start_hub.name: 0.0}
        # Dict to track the best path to reach each hub
        # We inicialice with a list thats why we put it like [self.start_hub]
        best_paths: dict[str, list[Hub]] = (
            {self.start_hub.name: [self.start_hub]}
            )
        # Set of hubs that have already been fully processed
        visited = set()

        while True:
            # Manual extraction of the unvisited
            # node with the lowest cumulative cost
            current_name = None
            min_cost = float('inf')

            for hub_name, cost in shortest_costs.items():
                if hub_name not in visited and cost < min_cost:
                    min_cost = cost
                    current_name = hub_name

            # If no node was found or the remainding ones are unreachable
            # we break
            if current_name is None or min_cost == float('inf'):
                break

            # If we reached the destination, we can stop early
            if current_name == self.end_hub.name:
                return best_paths[current_name]

            visited.add(current_name)
            current_path = best_paths[current_name]

            # Explore neighboring nodes
            for neighbor, base_cost in self.graph.get(current_name, []):
                if neighbor.name in visited:
                    continue

                # Add dynamic penalty cost if other drones are heavily
                # routing through this hub
                penalty = dynamic_penalties.get(neighbor.name, 0.0)
                new_cost = min_cost + base_cost + penalty

                # If this path to neighbor is shorter than any previous
                # path, record it
                if new_cost < shortest_costs.get(neighbor.name, float('inf')):
                    shortest_costs[neighbor.name] = new_cost
                    best_paths[neighbor.name] = current_path + [neighbor]
        return best_paths.get(self.end_hub.name, None)

    def find_all_paths(self, nb_drones: int) -> dict[int, list[Hub]]:
        """Calculates distinct paths for all drones minimizing
            simulation gridlocks
        Args:
            nb_drones: Total number of drones needing a computed itinerary
        Returns:
            Dictionary mapping each drone ID to its optimal list
            of sequential Hubs
        """
        paths_by_drone: dict[int, list[Hub]] = {}
        # Tracks accumulated routing congestion per hub name
        dynamic_penalties: dict[str, float] = {}

        for drone_id in range(1, nb_drones + 1):
            path = self._dijkstr(dynamic_penalties)
            if path is None:
                # Fallback to prevent crashes if the map is
                # physically disconnected
                paths_by_drone[drone_id] = [self.start_hub]
                continue
            paths_by_drone[drone_id] = path

            # Apply congestion penalty to intermediate nodes of the chosen path
            # (Excluding start and end since they have infinite capacity)
            for hub in path:
                if (
                    hub.name != self.start_hub.name
                    and hub.name != self.end_hub.name
                ):
                    # Increase cost dynamically so next
                    # drones consider alternative paths
                    # if this node becomes too crowded
                    dynamic_penalties[hub.name] = (
                                    dynamic_penalties.get(hub.name, 0.0) + 0.5
                                    )

        return paths_by_drone
