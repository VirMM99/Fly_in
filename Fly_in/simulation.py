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
        # Stores the raw movement lines (ex: "D1-A D2-B"). The turn prefix and
        # colors are presentation concerns handled by the main script.
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
        # Snapshots of the drone states seen at the start of turns without
        # movements. Used to distinguish legal waiting (subject VII.3 allows
        # drones to stay in place) from a real deadlock, where the exact same
        # state repeats forever because the simulation is deterministic.
        seen_states: set[tuple[tuple[int, bool], ...]] = set()

        while not all(drone.has_arrived() for drone in self.drones):
            self.current_turn += 1
            turn_moves: list[str] = []

            # Record the full drone state (path step + transit flag) before
            # processing the turn. If a turn executes no move, the state does
            # not change, so comparing these snapshots detects a true deadlock.
            state_snapshot = tuple(
                (drone.current_step, drone.in_transit_to_restricted)
                for drone in self.drones
            )

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
                    # The start hub has infinite capacity: parked drones there
                    # must not count toward occupancy.
                    if current_hub.name != self.start_hub.name:
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
                self.log_output.append(" ".join(turn_moves))
            else:
                # A turn without moves is allowed (strategic waiting). It only
                # becomes a deadlock when the exact same state was already seen
                # at the start of a previous empty turn: from there the
                # deterministic simulation would loop forever.
                if state_snapshot in seen_states:
                    raise RuntimeError(
                                    "Simulation deadlocked at turn"
                                    f" {self.current_turn}."
                                    "Verify pathfinding logic"
                                    )
                seen_states.add(state_snapshot)
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
