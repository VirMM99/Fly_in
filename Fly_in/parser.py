from hub import Hub
from connection import Connection
from pydantic import ValidationError


VALID_METADATA = {"zone", "color", "max_drones"}


class Parser:
    """Read and parse a drone map file"""
    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.nb_drones: int = 0
        self.start: Hub | None = None
        self.end: Hub | None = None
        self.hubs: list[Hub] = []
        self.hubs_by_name: dict[str, Hub] = {}
        self.connections: list[Connection] = []

    def parse(self) -> None:
        """Read the map file line by line"""
        # encoding is to save everithing in numbers of bytes
        # the archive is write using UTF-8, that represent any char
        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                for line_number, line in enumerate(file, start=1):
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
                        raise ValueError(f"Line {line_number}: Unknown line")

                if self.start is None:
                    raise ValueError("Missing start_hub")
                if self.end is None:
                    raise ValueError("Missing end_hub")
                if self.nb_drones <= 0:
                    raise ValueError("Missing nb_drones")
        except OSError as exc:
            raise ValueError("Cannot open file") from exc

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
    def _parse_hub_data(self, text: str, line_number: int) -> Hub:
        """Create a Hub object from text.
        Args:
            text: The raw text line belonging to the hub.
            line_number: Current line number for accurate error logging
        """
        metadata = self._parse_metadata(text)

        for key in metadata:
            if key not in VALID_METADATA:
                raise ValueError(f"Line {line_number}: Unknown metadata: {key}")

        if "[" in text:
            text = text.split("[")[0].strip()

        parts = text.split()
        if len(parts) != 3:
            raise ValueError(f"Line {line_number}: Invalid hub definition")

        name = parts[0]
        if " " in name:
            raise ValueError(f"Line {line_number}: Hub names cannot contain spaces")
        if "-" in name:
            raise ValueError(f"Line {line_number}: Hub names cannot contain '-'")

        try:
            return Hub(
                name=name,
                x=x[1],
                y=y[2],
                zone=metadata.get("zone", "normal"),
                color=metadata.get("color", "none"),
                max_drones=metadata.get("max_drones", "1")
            )
        except ValidationError as exc:
            errors = exc.errors()
            custom_msg = errors[0]["msg"] if errors else "Invalid values"
            raise ValueError(f"Line {line_number}: {custom_msg}") from exc

    def _parse_metadata(self, text: str) -> dict[str, str]:
        """Extract [metadata] from a hub or connection"""
        if text.count("[") > 1 or text.count("]") > 1:
            raise ValueError("Only one metadata block is allowed")
        if "[" not in text:
            return {}
        if "[" in text and not text.endswith("]"):
            raise ValueError("Metadata block not closed")

        metadata_text = text.split("[", maxsplit=1)[1]
        metadata_text = metadata_text.rstrip("]")

        metadata: dict[str, str] = {}

        for item in metadata_text.split():
            if "=" not in item:
                raise ValueError("Invalid metadata syntax")

            key, value = item.split("=", maxsplit=1)

            if key in metadata:
                raise ValueError(f"Duplicate metadata '{key}'")
            metadata[key] = value

        return metadata

    def parse_start(self, line: str) -> None:
        """Parse the start hub"""
        if self.start is not None:
            raise ValueError("Multiple start hubs")

        text = line.replace("start_hub:", "").strip()
        hub = self._parse_hub_data(text)
        hub.max_drones = 0

        if hub.name in self.hubs_by_name:
            raise ValueError(f"Duplicate start hub: {hub.name}")
        self.start = hub
        self.hubs_by_name[hub.name] = hub

    def parse_end(self, line: str) -> None:
        """Parse the end hub"""

        if self.end is not None:
            raise ValueError("Multiple end hubs")

        text = line.replace("end_hub:", "").strip()
        hub = self._parse_hub_data(text)
        hub.max_drones = 0

        if hub.name in self.hubs_by_name:
            raise ValueError(f"Duplicate end hub: {hub.name}")
        self.end = hub
        self.hubs_by_name[hub.name] = hub

    def parse_hub(self, line: str) -> None:
        """Parse a regular hub"""
        text = line.replace("hub:", "").strip()
        hub = self._parse_hub_data(text)
        if hub.name in self.hubs_by_name:
            raise ValueError(f"Duplicate hub: {hub.name}")
        self.hubs.append(hub)
        self.hubs_by_name[hub.name] = hub

    def parse_connection(self, line: str) -> None:
        """Parse a connection"""
        print("Connection")
