from hub import Hub
from connection import Connection


class Drone:
    """Represents a drone inside the simulation"""
    def __init__(self, drone_id: int, path: list[Hub]) -> None:
        self.id: int = drone_id
        # Ordered list of Hubs from start to end
        self.path: list[Hub] = path
        # Current index inside the path list
        self.current_step: int = 0
        self.in_transit_to_restricted: bool = False

    def get_current_hub(self) -> Hub:
        """Returns the current Hub the drone is positioned at"""
        return self.path[self.current_step]

    def get_next_hub(self) -> Hub | None:
        """Returns the next Hub in the path if available, otherwise None"""
        if self.current_step + 1 < len(self.path):
            return self.path[self.current_step + 1]
        return None

    def has_arrived(self) -> bool:
        """Checks if the drone has reached the destination hub"""
        return self.current_step == len(self.path) - 1


class Simulation:
    """Manages the simulation turn engine and map constraints"""
    def __init__(
            self,
            nb_drones: int,
            start_hub: Hub,
            end_hub: Hub,
            connections: list[Connection]
            ) -> None:
        self.nb_drones: int = nb_drones
        self.start_hub: Hub = start_hub
        self.end_hub: Hub = end_hub
        self.connections: list[Connection] = connections
        self.drones: list[Drone] = []
        self.current_turn: int = 0
        # Stores final output lines (ex: "T1: D1-A D2-B")
        self.log_output: list[str] = []

    def initialize_drones(self, paths_by_drone: dict[int, list[Hub]]) -> None:
        """Initializes all drones with paths
            computed by the pathfinder algorithm
        Args:
            paths_by_drone: Dictionary mapping drone
            IDs(1..N) to their list of Hubs
        """
        for drone_id in range(1, self.nb_drones + 1):
            path = paths_by_drone.get(drone_id, [self.start_hub])
            self.drones.append(Drone(drone_id, path))

    def run(self) -> list[str]:
        """Runs the turn-by-turn simulation
            until all drones reach the destination"""
        self.current_turn = 0
        self.log_output = []

        while not all(drone.has_arrived() for drone in self.drones):
            self.current_turn += 1
            turn_moves = []

            # Dict to manage capacity constraints for the current turn
            # Key: hub name -> number of drones
            # occupying or arriving at the hub
            # Track capacities for this specific turn snapshot
            hub_occupancy: dict[str, int] = {}
            # Key: (src_hub, dst_hub) -> num of drones
            # crossing the link this turn
            link_occupancy: dict[tuple[str, str], int] = {}

            # 1) Pre-Populate capacity based on drones that cannot or will
            # not move this turn
            for drone in self.drones:
                if drone.has_arrived():
                    continue
                if drone.in_transit_to_restricted:
                    #  Drone is currently inside the connection block,
                    # occupaying its target arrival hub capacity
                    target_hub = drone.get_next_hub()
                    if target_hub:
                        hub_occupancy[target_hub.name] = (
                            hub_occupancy.get(target_hub.name, 0) + 1
                            )
                else:
                    # Drone is static on its current hub for now
                    current_hub = drone.get_current_hub()
                    if current_hub.name != self.start_hub():
                        hub_occupancy[current_hub.name] = (
                            hub_occupancy.get(current_hub.name, 0) + 1
                            )

            # 2) Process actions for every drone
            for drone in self.drones:
                if drone.has_arrived():
                    continue

                # Case A: Drone was in flight to a restricted zone,
                # it MUST land now
                if drone.in_transit_to_restricted:
                    drone.current_step += 1
                    drone.in_transit_to_restricted = False
                    # Omitted from logs because the movement action was
                    # printed last turn
                    continue

                # Case B: Drone wants to initiate a new movement
                target_hub = drone.get_next_hub()
                if target_hub is None:
                    continue
                current_hub = drone.get_current_hub()

                # Capacity checks
                if (
                    target_hub.name != self.end_hub.name
                    and (
                        hub_occupancy.get(target_hub.name, 0)
                        >= target_hub.max_drones
                    )
                ):
                    continue

                conn_obj = self._get_connection(current_hub, target_hub)
                max_link = conn_obj.max_link_capacity if conn_obj else 1
                connection_key = (current_hub.name, target_hub.name)
                reverse_key = (target_hub.name, current_hub.name)

                active_links = link_occupancy.get(connection_key, 0) + (
                                    link_occupancy.get(reverse_key, 0)
                                    )
                if active_links >= max_link:
                    continue

                # Free old space if applicable
                if current_hub.name != self.start_hub.name:
                    hub_occupancy[current_hub.name] = max(
                        0, hub_occupancy.get(current_hub.name, 1) - 1
                        )

                # Reserve new spaces
                link_occupancy[connection_key] = (
                    link_occupancy.get(connection_key, 0) + 1
                    )

                if target_hub.zone == "restricted":
                    # Transit format: D<ID>-<hub1>-<hub2>
                    turn_moves.append(
                            f"D{drone.id}-{current_hub.name}-{target_hub.name}"
                            )
                    drone.in_transit_to_restricted = True
                    hub_occupancy[target_hub.name] = (
                        hub_occupancy.get(target_hub.name, 0) + 1
                        )
                else:
                    # Normal or priority move (1 turn)
                    drone.current_step += 1
                    turn_moves.append(f"D{drone.id}-{target_hub.name}")
                    if target_hub.name != self.end_hub.name:
                        hub_occupancy[target_hub.name] = (
                            hub_occupancy.get(target_hub.name, 0) + 1
                            )

            # Store current turn logs if any moves were executed
            if turn_moves:
                # Sort alphabetically by drone ID for standardized output
                turn_moves.sort(
                    key=lambda x: int(x.split("-")[0].replace("D", ""))
                    )
                self.log_output.append(
                                    f"T{self.current_turn}: "
                                    + " ".join(turn_moves))
            else:
                # Prevent infinite loops if map
                # is blocked or routing is invalid
                raise RuntimeError(
                                    "Simulation deadlocked at turn"
                                    f" {self.current_turn}."
                                    "Verify pathfinding logic"
                                    )
        return self.log_output

    def _get_connection(self, hub1: Hub, hub2: Hub) -> Connection | None:
        """Finds the bidirectional Connection object between two Hubs"""
        for conn in self.connections:
            if (
                (conn.hub1.name == hub1.name
                    and conn.hub2.name == hub2.name)
                or (conn.hub1.name == hub2.name
                    and conn.hub2.name == hub1.name)
            ):
                return conn
        return None
