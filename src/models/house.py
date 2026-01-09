"""House data model."""

from datetime import datetime
from pydantic import BaseModel, Field

from .scores import VisionAnalysis, PresentFitScore, PotentialScore


class HouseFeatures(BaseModel):
    """Structured features extracted from listing."""

    bedrooms: int | None = None
    bathrooms: float | None = None
    sqft: int | None = None
    lot_sqft: int | None = None
    year_built: int | None = None
    property_type: str = ""  # single family, condo, townhouse
    parking: str = ""  # garage, carport, street
    hoa_fee: int | None = None
    heating: str = ""
    cooling: str = ""
    flooring: list[str] = Field(default_factory=list)
    appliances: list[str] = Field(default_factory=list)


class House(BaseModel):
    """Complete house object with all data."""

    # Identity
    id: str = Field(description="Unique identifier for this house")
    url: str = Field(default="", description="Source listing URL")

    # Basic info
    address: str = Field(default="")
    city: str = Field(default="")
    state: str = Field(default="")
    zip_code: str = Field(default="")

    # Geolocation
    latitude: float | None = Field(default=None, description="Latitude coordinate")
    longitude: float | None = Field(default=None, description="Longitude coordinate")
    price: int | None = Field(default=None, description="Listing price in dollars")

    # Description
    description: str = Field(default="", description="Listing description text")

    # Features
    features: HouseFeatures = Field(default_factory=HouseFeatures)

    # Images
    image_urls: list[str] = Field(default_factory=list, description="URLs of listing images")

    # Analysis results (populated by agents)
    vision_analysis: VisionAnalysis | None = None
    present_fit_score: PresentFitScore | None = None
    potential_score: PotentialScore | None = None
    brief: str = Field(default="", description="Generated house brief markdown")

    # User annotations
    annotations: list[str] = Field(default_factory=list, description="User feedback and notes")
    user_verdict: str | None = Field(default=None, description="User's final verdict: liked, disliked, shortlisted")

    # Timestamps
    ingested_at: datetime = Field(default_factory=datetime.now)
    scored_at: datetime | None = None

    @classmethod
    def create_from_zillow(
        cls,
        house_id: str,
        url: str,
        address: str,
        price: int | None,
        image_urls: list[str],
        description: str = "",
        features: dict | None = None,
    ) -> "House":
        """Factory method to create house from Zillow data."""
        return cls(
            id=house_id,
            url=url,
            address=address,
            price=price,
            image_urls=image_urls,
            description=description,
            features=HouseFeatures(**(features or {})),
        )
