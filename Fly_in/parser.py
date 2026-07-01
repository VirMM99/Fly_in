from typing import Any


class Parser:
    """Read and parse a drone map file"""
    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.nb_drones: int = 0
        self.start: dict[str, Any] | None = None
        self.end: dict[str, Any] | None = None
        self.hubs: list[dict[str, Any]] = []
        # Is list tuple because it has two names
        self.connections: list[tuple[str, str]] = []

    def parse(self):
        """Read the map file line by line"""
        # encoding is to save everithing in numbers of bytes
        # the archive is write usidng UTF-8, that represent any char
        with open(self.filename, "r", encoding="utf-8") as file:
            for line in file:
                # To delete \n
                line = line.strip()
                # Ignore empty lines
                if not line:
                    continue
                # Ignore commets
                if line.startswith("#"):
                    continue

                print(line)

                if line.startswith("nb_drones:"):
                    self.parse_nb_drones(line)
                elif line.startswith("start_hub:"):
                    self.parse_start(line)
                elif line.startswith("end_hub:"):
                    self.parse_end(line)
                elif line.startswith("hub:"):
                    self.parse_hub(line)
                elif line.startswith("connection:"):
                    self.parse_connection(line)

    def parse_nb_drones(self, line: str) -> None:
        """Parse the number of drones"""
        text = line.replace("nb_drones:", "").strip()
        self.nb_drones = int(text)

    def parse_start(self, line: str) -> None:
        """Parse the start hub"""
        print("Start hub")

    def parse_end(self, line: str) -> None:
        """Parse the end hub"""
        print("End hub")

    def parse_hub(self, line: str) -> None:
        """Parse a regular hub"""
        print("Hub")

    def parse_connection(self, line: str) -> None:
        """Parse a connection"""
        print("Connection")


# self.hubs.append(...)

# number = int(...)
# parts = text.split()
# name = parts[0]
# x = int(parts[1])
# y = int(parts[2])

# first, second = text.split("-")

# number_of_drones = 5

# start = Hub(...)
# end = Hub(...)

# graph = {
#     "hub": ["roof1"],
#     "roof1": ["hub", "roof2"],
#     "roof2": ["roof1", "goal"]
# }
