from beanie import Document
from typing import Optional
from pydantic import Field


class PlaceDoc(Document):
    id: int  # GNIS FEATURE_ID (INCITS 446-2008) - https://geonames.usgs.gov/domestic/index.html
    name: str
    clazz: str = Field(alias="class")  # 'class' is a reserved keyword in Python
    state: str
    state_fips: str
    state_name: str
    county: Optional[str] = None
    county_fips: Optional[str] = None
    country: str
    country_name: str
    latitude_dms: Optional[str] = None
    longitude_dms: Optional[str] = None
    latitude_dec: float
    longitude_dec: float
    elevation_meters: Optional[int] = None
    elevation_feet: Optional[int] = None

    class Settings:
        name = "places"