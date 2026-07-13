import sys
from parser import Parser
from pathfinder import Pathfinder
from simulation import Simulation

# ANSI Escape secuences from terminal coloring 
# w/out external libraries
ANSI_COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "gray": "\033[90m",
    "white": "\033[97m",
    "none": "\033[0m"
}
ANSI_RESET = "\033[0m"

def colorize_log(log_line: str, hubs_by_name: dict) -> str:
    """Colorizes terminal output tokens according to the metadata
        properties of targeted hubs
    """
    parts = log_line.split(" ")
    turn_prefix = parts[0]
    movements = parts[1:]

    colored_moves = []
    for move in movements:
        # Check if it's a restricted transition link(ex:D1-roof1-roof2)
        if move.count("-") == 2:
            drone_part, src_name, dst_name = move.split("-")
            hub_obj = hubs_by_name.get(dst_name)
            color_code = ANSI_COLORS.get(hub_obj.color.lower(), ANSI_COLORS["none"]) if hub_obj else ""
            colored_moves.append(f"{drone_part}-{src_name}->{color_code}{dst_name}{ANSI_RESET}")
        else:
            # Normal movement(ex:D1-roof1)
            drone_part, dst_name = move.split("-")
            hub_obj =hubs_by_name.get(dst_name)
            color_code = ANSI_COLORS.get(hub_obj.color.lower(), ANSI_COLORS["none"]) if hub_obj else ""
            colored_moves.append(f"{drone_part}-{color_code}{dst_name}{ANSI_RESET}")
    return f"{turn_prefix}" + " ".join(colored_moves)

def main() -> None:
    """Main execution function handling parameters, routing,
        execution and coloring rendering
    """
    if len(sys.argv) != 2:
        print("Usage: Python main.py <map_file>", file=sys.stderr)
        sys.exit(1)

    map_filename = sys.argv[1]

    try:
        # 1)Parse the map
        parser = Parser(map_filename)
        parser.parse()

        # 2)Compute routes
        pathfinder = Pathfinder(
            start_hub=parser.start,
            end_hub=parser.end,
            hubs=parser.hubs,
            connections=parser.connections
        )
        paths_by_drone = pathfinder.find_all_paths(parser.nb_drones)

        # 3)Simulate operations
        simulation = Simulation(
            nb_drones=parser.nb_drones,
            start_hub=parser.start,
            end_hub=parser.end,
            connections=parser.connections
        )
        simulation.initialize_drones(paths_by_drone)
        log_output = simulation.run()

        # 4)Print beautiful colored terminal output matching
        # subject metadata requirements
        print(
            f"\n{ANSI_COLORS['cyan']}=== SIMULATION START "
            f"({parser.nb_drones} Drones) ==={ANSI_RESET}"
            )
        for turn_log in log_output:
            print(colorize_log(turn_log, parser.hubs_by_name))
        print(
            f"{ANSI_COLORS['cyan']}==== TARGET REACHED SUCCESSFULLY "
            f"==={ANSI_RESET}\n"
            )
    except ValueError as exc:
        print(f"\033[91mERROR: {exc}\033[0m", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"\033[91mSimulation Deadlock: {exc}\033[0m", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()