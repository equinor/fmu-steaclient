from datetime import datetime, date
from typing import Dict, Optional

from pydantic import (
    BaseModel,
    conlist,
    field_validator,
    Field,
    model_validator,
    ConfigDict,
)
from typing_extensions import Self

from .stea_keys import SteaKeys


def replace_dash(string: str) -> str:
    return string.replace("_", "-")


class SimulatorProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=replace_dash)
    ecl_key: str = Field(description="Summary key")
    start_date: Optional[date] = Field(
        None,
        description=(
            "By default fmu-steaclient will calculate a profile from the full "
            "time range of the simulated data, but you can optionally use the keywords "
            "start_date and end_year to limit the time range. Production on the "
            "start_date is included. Date format is YYYY-MM-DD."
        ),
    )
    start_year: Optional[int] = Field(None, description="Deprecated. Use start_date")
    end_year: Optional[int] = Field(
        None,
        description=(
            "Set an explicit last year for the data to extract from a profile. All "
            "data up until the last day of this year will be included."
        ),
    )
    mult: Optional[conlist(float, min_length=1)] = Field(
        None, description="List of multipliers of summary key"
    )
    glob_mult: Optional[float] = Field(
        None, description="A single global multiplier of summary key"
    )

    @model_validator(mode="after")
    def check_start_year(self) -> Self:
        if self.start_year is not None and self.start_date is not None:
            raise ValueError("Do not provide both start_year and start_date")
        if self.start_year:
            self.start_date = date(self.start_year, 1, 1)
        return self


class Profile(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=replace_dash)
    start_year: int = Field(
        description="Start year",
    )
    data: Optional[conlist(float, min_length=1)] = Field(
        description="Values",
    )


class SteaConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=replace_dash)
    config_date: datetime = Field(
        description="date or timestamp: YYYY-MM-DD (HH:MM:SS) "
        "that comes with stea request",
    )
    project_id: int = Field(
        description=(
            "The id of the project, which must already exist and be available in the "
            "stea database. In the Stea documentation this is called 'AlternativeId'"
        ),
    )
    project_version: int = Field(
        description="Project alternative version number that comes from stea database",
    )
    profiles: Dict[str, Profile] = Field(
        {},
        description=(
            "The profiles keyword is used to enter profile data explicitly in the "
            "configuration file. Each profile is identified with an id from the "
            "existing stea project, a start year and the actual data."
        ),
    )
    ecl_profiles: Dict[str, SimulatorProfile] = Field(
        description=(
            "Profiles which are calculated directly from a reservoir simulation. "
            "They are listed with the ecl-profiles ecl_key."
        ),
    )
    results: conlist(str, min_length=1) = Field(
        description="Specify what STEA should calculate"
    )
    ecl_case: Optional[str] = Field(None, description="ecl case location")
    stea_server: str = Field(
        SteaKeys.PRODUCTION_SERVER,
        description="stea server host",
    )

    @field_validator("ecl_profiles")
    @classmethod
    def non_empty(cls, value: dict):
        assert len(value) != 0, "Can not be empty"
        return value
