from hub import Hub


class Parser:
    """Read and parse a drone map file"""
    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.nb_drones: int = 0
        self.start: Hub | None = None
        self.end: Hub | None = None
        self.hubs: list[Hub] = []
        self.connections: list[tuple[str, str]] = []

    def parse(self) -> None:
        """Read the map file line by line"""
        # encoding is to save everithing in numbers of bytes
        # the archive is write using UTF-8, that represent any char
        with open(self.filename, "r", encoding="utf-8") as file:
            for line in file:
                # To delete \n
                line = line.strip()
                # Ignore empty lines
                if not line:
                    continue
                # Ignore comments
                if line.startswith("#"):
                    continue

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
                else:
                    raise ValueError(f"Unknown line: {line}")

    def parse_nb_drones(self, line: str) -> None:
        """Parse the number of drones"""
        text = line.replace("nb_drones:", "").strip()
        try:
            self.nb_drones = int(text)
        except ValueError as exc:
            raise ValueError("nb_drones must be an integer") from exc
        if self.nb_drones <= 0:
            raise ValueError("nb_drones must be positive")

    # To separate the hub from the metadata so we can read
    def _parse_hub_data(self, text: str) -> Hub:
        """Create a Hub object from text"""
        metadata = self._parse_metadata(text)

        VALID_METADATA = {"zone", "color", "max_drones"}
        for key in metadata:
            if key not in VALID_METADATA:
                raise ValueError(f"Unknown metadata: {key}")
        VALID_ZONES = {"normal", "blocked", "restricted", "priority"}
        zone = metadata.get("zone", "normal")
        if zone not in VALID_ZONES:
            raise ValueError(f"Invalid zone type: {zone}")

        if "[" in text:
            text = text.split("[")[0].strip()

        parts = text.split()
        if len(parts) != 3:
            raise ValueError("Invalid hub definition")
        name = parts[0]
        if "-" in name:
            raise ValueError("Hub names cannot contain '-'")

        try:
            x = int(parts[1])
            y = int(parts[2])
        except ValueError as exc:
            raise ValueError("Coordinates must be integers") from exc


        color = metadata.get("color", "none")
        try:
            max_drones = int(metadata.get("max_drones", "1"))
        except ValueError as exc:
            raise ValueError("max_drones must be an integer") from exc
        if max_drones <= 0:
            raise ValueError("max_drones must be positive")

        return Hub(
            name=name,
            x=x,
            y=y,
            zone=zone,
            color=color,
            max_drones=max_drones
        )

    def _parse_metadata(self, text: str) -> dict[str, str]:
        """Extract [metadata] from a hub or connection"""
        if "[" not in text:
            return {}

        metadata_text = text.split("[", maxsplit=1)[1]
        metadata_text = metadata_text.rstrip("]")

        metadata: dict[str, str] = {}

        for item in metadata_text.split()
            if "=" not in item:
                raise ValueError("Invalid metadata syntax")

            key, value = item.split("=", maxsplit=1)
            metadata[key] = value

        return metadata

    def parse_start(self, line: str) -> None:
        """Parse the start hub"""
        text = line.replace("start_hub:", "").strip()
        if self.start is not None:
            raise ValueError("Multiple start hubs")
        self.start = self._parse_hub_data(text)

    def parse_end(self, line: str) -> None:
        """Parse the end hub"""
        text = line.replace("end_hub:", "").strip()
        if self.end is not None:
            raise ValueError("Multiple end hubs")
        self.end = self._parse_hub_data(text)

    def parse_hub(self, line: str) -> None:
        """Parse a regular hub"""
        text = line.replace("hub:", "").strip()
        self.hubs.append(self._parse_hub_data(text))

    def parse_connection(self, line: str) -> None:
        """Parse a connection"""
        print("Connection")
