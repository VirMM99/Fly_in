from hub import Hub
from connection import Connection

class Drone:
    """Representes a drone inside the simulation"""
    def __init__(self, drone_id: int, path: list[Hub]) -> None:
        self.id: int = drone_id
        # Ordered list of Hubs from start to end
        self.path: list[Hub] = path
        # Current index inside the path list
        self.current_step: int = 0
        # Remaining turns to wait before moving again
        self.turns_remaining: int = 0

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
    """Manages the simulation turn engine and map constrains"""
    def __init__(self, nb_drones: int, start_hub: Hub, end_hub: Hub, connections: list[Connection]) -> None:
        self.nb_drones: int = nb_drones
        self.start_hub: Hub = start_hub
        self.end_hub: Hub = end_hub
        self.connections: list[Connection] = connections

        self.drones: list[Drone] = []
        self.current_turn: int = 0
        # Stores final output lines (ex: "T1: D1-A D2-B")
        self.log_output: list[str] = []

    def initialize_drones(self, paths_by_drone: dict[int, list[Hub]]) -> None:
        """Initializes all drones with paths computed by the pathfinder algorithm
        Args:
            paths_by_drone: Dictionary mapping drone IDs(1..N) to their list of Hubs
        """
        for drone_id in range(1, self.nb_drones + 1):
            path = paths_by_drone.get(drone_id, [self.start_hub])
            self.drones.append(Drone(drone_id, path))

    def run(self) -> list[str]:
        """Runs the turn-by-turn simulation until all drones reach the destination"""
        self.current_turn = 0
        self.log_output = []

        while not all(drone.has_arrived() for drone in self.drones):
            self.current_turn += 1
            turn_moves = []

            # Dict to manage capacity constrains for the current turn
            # Key: hub name -> number of drones occupying or arriving at the hub
            hub_occupancy: dict[str, int] = {}

            # Populate occupancy with drones that are static os still waiting
            # out a restriction
            for drone in self.drones:
                if drone.has_arrived() or drone.turns_remaining > 0:
                    current_hub_name = drone.get_current_hub().name
                    hub_occupancy[current_hub_name] = hub_occupancy.get(current_hub_name, 0) + 1

            # Key: (src_hub, dst_hub) -> num of drones crossing the link this turn
            link_occupancy: dict[tuple[str, str], int] = {}

            # Process delayed drones traversing restricted zones
            for drone in self.drones:
                if drone.turns_remaining > 0:
                    drone.turns_remaining -= 1

            # Try to move stationary drones standing at a hub
            for drone in self.drones:
                # If already arrived or still mid-transit (waiting turns), 
                # it cannot initiate a new move
                if drone.has_arrived() or drone.turns_remaining > 0:
                    continue
                target_hub = drone.get_next_hub()
                if target_hub is None:
                    continue

                # Contrain validation: Check max_drones capacity at target hub
                current_hub_drones= hub_occupancy.get(target_hub.name, 0)
                if current_hub_drones >= target_hub.max_drones:
                    continue
                # Check max_link_capacity for the chosen connection
                current_drone_hub = drone.get_current_hub()
                connection_key = (current_drone_hub.name, target_hub.name)
                conn_obj = self._get_connection(current_drone_hub, target_hub)
                max_link = conn_obj.max_link_capacity if conn_obj else 1

                current_link_drones = link_occupancy.get(connection_key, 0)
                if current_link_drones >= max_link:
                    continue

                # Execute move: register turn tracking occupancies
                hub_occupancy[target_hub.name] = current_hub_drones + 1
                link_occupancy[connection_key] = current_link_drones + 1
                # Update step immediately so the log reflects the destination hub
                drone.current_step += 1
                turn_moves.append(f"D{drone.id}-{target_hub.name}")
                # Apply cost depending on the destination zone type
                if target_hub.zone == "restricted":
                    # Requires 2 turns total: 1 turn to move(this one)+1 turn locked waiting
                    drone.turns_remaining = 1
                else:
                    # Normal zone requires exactly 1 turn total(ready to move next turn)
                    drone.turns_remaining = 0
            # Store current turn logs if any moves were executed
            if turn_moves:
                # Sort alphabetically by drone ID for standardized output
                turn_moves.sort(key=lambda x: int(x.split("-")[0].replace("D", "")))
                self.log_output.append(f"T{self.current_turn}: " + " ".join(turn_moves))
            else:
                # Prevent infinite loops if map is blocked or routing is invalid
                raise RuntimeError(f"Simulation deadlocked at turn {self.current_turn}. Verify pathfinding logic")
        return self.log_output

    def _get_connection(self, hub1: Hub, hub2: Hub) -> Connection | None:
        """Finds the bidirectional Connection object between two Hubs"""
        for conn in self.connections:
            if  (conn.hub1.name == hub1.name and conn.hub2.name == hub2.name) or \
                (conn.hub1.name == hub2.name and conn.hub2.name == hub1.name):
                return conn
        return None
