import sys
from hub import Hub
from parser import Parser
from pathfinder import Pathfinder
from simulation import Simulation

# ANSI escape sequences for terminal coloring without external libraries
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


def colorize_log(log_line: str, hubs_by_name: dict[str, Hub]) -> str:
    """Colorize one raw movement line using each destination hub's color.

    The visual mode enriches the subject's exact format: restricted transits
    (D<ID>-<hub1>-<hub2>) are rendered as D<ID>-<hub1>-><hub2> with the
    target hub colored.
    """
    colored_moves = []
    for move in log_line.split(" "):
        # Restricted in-flight movement, e.g. "D1-roof1-roof2"
        if move.count("-") == 2:
            drone_part, src_name, dst_name = move.split("-")
            hub_obj = hubs_by_name.get(dst_name)
            color_key = hub_obj.color.lower() if hub_obj else "none"
            color_code = ANSI_COLORS.get(color_key, "")
            colored_moves.append(
                f"{drone_part}-{src_name}->"
                f"{color_code}{dst_name}{ANSI_RESET}"
            )
        else:
            # Normal movement, e.g. "D1-roof1"
            drone_part, dst_name = move.split("-")
            hub_obj = hubs_by_name.get(dst_name)
            color_key = hub_obj.color.lower() if hub_obj else "none"
            color_code = ANSI_COLORS.get(color_key, "")
            colored_moves.append(
                f"{drone_part}-{color_code}{dst_name}{ANSI_RESET}"
            )

    return " ".join(colored_moves)


def main() -> None:
    """Main execution handling parameters, routing, execution and rendering.

    Accepts an optional "--raw" flag that prints the exact subject output
    format: one movement line per turn, no colors, no turn prefixes and no
    banners. Without it, renders the colored visual representation.
    """
    if (
        len(sys.argv) not in (2, 3)
        or (len(sys.argv) == 3 and sys.argv[2] != "--raw")
    ):
        print("Usage: Python main.py <map_file> [--raw]", file=sys.stderr)
        sys.exit(1)

    map_filename = sys.argv[1]
    raw_mode = len(sys.argv) == 3 and sys.argv[2] == "--raw"

    try:
        # 1) Parse the map
        parser = Parser(map_filename)
        parser.parse()

        # Explicit validation
        if parser.start is None or parser.end is None:
            raise ValueError(
                "Parser failed to define valid start or end hubs"
            )
        # 2) Compute routes
        pathfinder = Pathfinder(
            start_hub=parser.start,
            end_hub=parser.end,
            hubs=parser.hubs,
            connections=parser.connections
        )
        paths_by_drone = pathfinder.find_all_paths(parser.nb_drones)

        # 3) Simulate operations
        simulation = Simulation(
            nb_drones=parser.nb_drones,
            start_hub=parser.start,
            end_hub=parser.end,
            connections=parser.connections
        )
        simulation.initialize_drones(paths_by_drone)
        log_output = simulation.run()

        # 4) Render: --raw matches the subject's exact format, otherwise the
        # colored visual representation with turn labels and banners.
        if raw_mode:
            for turn_log in log_output:
                print(turn_log)
        else:
            print(
                f"\n{ANSI_COLORS['cyan']}=== SIMULATION START "
                f"({parser.nb_drones} Drones) ==={ANSI_RESET}"
                )
            for turn_number, turn_log in enumerate(log_output, start=1):
                colored_line = (
                    f"T{turn_number}: "
                    f"{colorize_log(turn_log, parser.hubs_by_name)}"
                )
                print(colored_line)
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
