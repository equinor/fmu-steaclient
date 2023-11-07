import datetime
import sys
from typing import List, Optional

from resdata.summary import Summary

from .stea_keys import SteaKeys


def date_string(timestamp):
    return timestamp.strftime("%Y-%m-%dT%H:%M:%S")


BARRELS_PR_SM3 = 6.2898


class SteaRequest:
    units = {"Bbl": {"SM3": BARRELS_PR_SM3}, "Sm3": {"SM3": 1.0}}

    scale_factors = {"1": 1.0, "Mill": 1.0e-6, "1000 Mill": 1.0e-9}

    def __init__(self, stea_input, project):
        self.stea_input = stea_input
        self.project = project
        self.request_data = {
            SteaKeys.PROJECT_ID: project.project_id,
            SteaKeys.PROJECT_VERSION: project.project_version,
            SteaKeys.CONFIG_DATE: date_string(stea_input.config_date),
            SteaKeys.RESULTS: stea_input.results,
            SteaKeys.ADJUSTMENTS: {SteaKeys.PROFILES: []},
        }

    def add_profile(self, profile_id, start_year, data):
        if not self.project.has_profile(profile_id):
            raise KeyError(f"Invalid profile id: {profile_id} for this project")

        profile_data = {
            SteaKeys.PROFILE_ID: profile_id,
            SteaKeys.DATA_OUTER: {
                SteaKeys.DATA_INNER: data,
                SteaKeys.START_YEAR: start_year,
            },
        }

        self.request_data[SteaKeys.ADJUSTMENTS][SteaKeys.PROFILES].append(profile_data)

    def data(self):
        return self.request_data

    def add_ecl_profile(
        self,
        profile_id: str,
        key: str,
        start_date: Optional[datetime.date] = None,
        end_year: Optional[int] = None,
        multiplier: Optional[List[float]] = None,
        global_multiplier: float = 1,
    ):
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals
        if multiplier is None:
            multiplier = [1]

        if self.stea_input.ecl_case is None:
            raise ValueError(
                "When adding ecl_profile you must configure an Eclipse case"
            )

        case: Summary = self.stea_input.ecl_case
        if key not in case:
            raise KeyError(f"No such summary key: {key}")

        if start_date is None:
            start_date = case.start_date

        if end_year is None:
            end_date = case.end_date
        else:
            end_date = datetime.date(end_year, 12, 31)
            # only the year part of this date is used by time_range()

        start_year_jan1 = datetime.date(start_date.year, 1, 1)
        time_range_to_crop = None
        if start_date > start_year_jan1 and start_date > case.start_date:
            # Profile must be cropped with a finer than yearly resolution,
            # ecl's time_range and blocked_productions do not support this directly:
            time_range_to_crop = case.time_range(
                start=datetime.date(start_date.year, 1, 1),
                end=start_date,
                interval="1d",
            )

        time_range = case.time_range(start=start_year_jan1, end=end_date, interval="1y")
        ecl_unit = case.unit(key)

        unit = self.project.get_profile_unit(profile_id)
        mult = self.project.get_profile_mult(profile_id)
        if unit in self.units and ecl_unit in self.units[unit]:
            unitfactor = self.units[unit][ecl_unit]
        else:
            unitfactor = 1.0
            sys.stdout.write(
                f"Default conversion between {unit} and {ecl_unit} to 1.\n"
            )
        unit_conversion = unitfactor * self.scale_factors[mult]
        data = list(case.blocked_production(key, time_range) * unit_conversion)

        if time_range_to_crop is not None:
            deduct = list(
                case.blocked_production(key, time_range_to_crop) * unit_conversion
            )
            data[0] -= sum(deduct)

        mult_rangeend = min(len(multiplier), len(data))
        data[:mult_rangeend] = map(
            lambda x, y: x * y, data[:mult_rangeend], multiplier[:mult_rangeend]
        )

        data = [x * global_multiplier for x in data]
        self.add_profile(profile_id, start_date.year, data)
