from hub import Hub


class Parser:
    """Read and parse a drone map file"""
    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.nb_drones: int = 0
        self.start: Hub | None = None
        self.end: Hub | None = None
        self.hubs: list[Hub] = []
        # Is list tuple because it has two names
        self.connections: list[tuple[str, str]] = []

    def parse(self) -> None:
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

    # To separate the hub from the metadata so we can read
    def _parse_hub_data(self, text: str) -> Hub:
        """Create a Hub object from text"""
        if "[" in text:
            text = text.split("[")[0].strip()
        parts = text.split()
        if len(parts) != 3:
            raise ValueError("Invalid hub definition")
        name = parts[0]
        x = int(parts[1])
        y = int(parts[2])

        return Hub(
            name=name,
            x=x,
            y=y
        )

    def parse_start(self, line: str) -> None:
        """Parse the start hub"""
        text = line.replace("start_hub:", "").strip()
        self.start = self._parse_hub_data(text)

    def parse_end(self, line: str) -> None:
        """Parse the end hub"""
        text = line.replace("end_hub:", "").strip()
        self.end = self._parse_hub_data(text)

    def parse_hub(self, line: str) -> None:
        """Parse a regular hub"""
        text = line.replace("hub:", "").strip()
        self.hubs.append(self._parse_hub_data(text))

    def parse_connection(self, line: str) -> None:
        """Parse a connection"""
        print("Connection")
