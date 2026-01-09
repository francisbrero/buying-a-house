"""JSON file-based storage for houses and taste model."""

import json
from pathlib import Path
from datetime import datetime

from src.models.house import House
from src.models.taste import TasteModel


class JsonStore:
    """JSON file storage for house evaluator data."""

    def __init__(self, data_dir: Path | str = "data"):
        self.data_dir = Path(data_dir)
        self.houses_dir = self.data_dir / "houses"
        self.taste_file = self.data_dir / "taste.json"
        self.aesthetics_file = self.data_dir / "aesthetics.md"

        # Ensure directories exist
        self.houses_dir.mkdir(parents=True, exist_ok=True)

    # House operations

    def save_house(self, house: House) -> Path:
        """Save a house to JSON file."""
        file_path = self.houses_dir / f"{house.id}.json"
        with open(file_path, "w") as f:
            json.dump(house.model_dump(mode="json"), f, indent=2, default=str)
        return file_path

    def load_house(self, house_id: str) -> House | None:
        """Load a house by ID."""
        file_path = self.houses_dir / f"{house_id}.json"
        if not file_path.exists():
            return None
        with open(file_path) as f:
            data = json.load(f)
        return House.model_validate(data)

    def list_houses(self) -> list[House]:
        """List all houses."""
        houses = []
        for file_path in self.houses_dir.glob("*.json"):
            with open(file_path) as f:
                data = json.load(f)
            houses.append(House.model_validate(data))
        return sorted(houses, key=lambda h: h.ingested_at, reverse=True)

    def delete_house(self, house_id: str) -> bool:
        """Delete a house by ID."""
        file_path = self.houses_dir / f"{house_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    # Taste operations

    def save_taste(self, taste: TasteModel) -> Path:
        """Save the taste model."""
        with open(self.taste_file, "w") as f:
            json.dump(taste.model_dump(mode="json"), f, indent=2)
        return self.taste_file

    def load_taste(self) -> TasteModel | None:
        """Load the taste model."""
        if not self.taste_file.exists():
            return None
        with open(self.taste_file) as f:
            data = json.load(f)
        return TasteModel.model_validate(data)

    def load_or_create_taste(self) -> TasteModel:
        """Load taste model or create empty one."""
        taste = self.load_taste()
        if taste is None:
            taste = TasteModel.create_empty()
            self.save_taste(taste)
        return taste

    def taste_exists(self) -> bool:
        """Check if taste model exists."""
        return self.taste_file.exists()

    # Aesthetics.md operations

    def save_aesthetics(self, content: str) -> Path:
        """Save aesthetics.md file."""
        with open(self.aesthetics_file, "w") as f:
            f.write(content)
        return self.aesthetics_file

    def load_aesthetics(self) -> str | None:
        """Load aesthetics.md content."""
        if not self.aesthetics_file.exists():
            return None
        with open(self.aesthetics_file) as f:
            return f.read()

    # Utility methods

    def generate_house_id(self, address: str) -> str:
        """Generate a unique house ID from address."""
        # Simple slug from address
        slug = address.lower()
        slug = "".join(c if c.isalnum() or c == " " else "" for c in slug)
        slug = "-".join(slug.split())[:50]

        # Add timestamp suffix for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{slug}-{timestamp}" if slug else f"house-{timestamp}"

    def normalize_address(self, address: str) -> str:
        """Normalize address for comparison."""
        # Lowercase and remove extra whitespace
        addr = " ".join(address.lower().split())
        # Remove punctuation except spaces
        addr = "".join(c if c.isalnum() or c == " " else " " for c in addr)
        # Normalize common abbreviations
        replacements = {
            " st ": " street ",
            " st$": " street",
            " dr ": " drive ",
            " dr$": " drive",
            " ave ": " avenue ",
            " ave$": " avenue",
            " rd ": " road ",
            " rd$": " road",
            " ln ": " lane ",
            " ln$": " lane",
            " ct ": " court ",
            " ct$": " court",
            " cir ": " circle ",
            " cir$": " circle",
            " blvd ": " boulevard ",
            " blvd$": " boulevard",
            " pl ": " place ",
            " pl$": " place",
        }
        for abbr, full in replacements.items():
            if abbr.endswith("$"):
                if addr.endswith(abbr[:-1]):
                    addr = addr[:-len(abbr)+1] + full
            else:
                addr = addr.replace(abbr, full)
        # Collapse multiple spaces
        return " ".join(addr.split())

    def house_exists(self, address: str) -> bool:
        """Check if a house with this address already exists."""
        normalized = self.normalize_address(address)
        for house in self.list_houses():
            if self.normalize_address(house.address) == normalized:
                return True
        return False

    def find_house_by_address(self, address: str) -> House | None:
        """Find a house by address (normalized comparison)."""
        normalized = self.normalize_address(address)
        for house in self.list_houses():
            if self.normalize_address(house.address) == normalized:
                return house
        return None

    def bulk_save_houses(self, houses: list[House]) -> tuple[int, int]:
        """Save multiple houses, skipping duplicates.

        Returns (saved_count, skipped_count).
        """
        saved = 0
        skipped = 0
        for house in houses:
            if self.house_exists(house.address):
                skipped += 1
            else:
                self.save_house(house)
                saved += 1
        return saved, skipped

    def get_unscored_houses(self) -> list[House]:
        """Get houses that haven't been scored yet."""
        return [h for h in self.list_houses() if h.present_fit_score is None]

    def get_scored_houses(self) -> list[House]:
        """Get houses that have been scored, sorted by score."""
        scored = [h for h in self.list_houses() if h.present_fit_score is not None]
        return sorted(
            scored,
            key=lambda h: h.present_fit_score.score if h.present_fit_score else 0,
            reverse=True,
        )
