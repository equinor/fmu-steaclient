import datetime
import sys

from ecl.summary import EclSum

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
        profile_id,
        key,
        first_year=None,
        last_year=None,
        multiplier=None,
        global_multiplier=1,
    ):
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals
        if multiplier is None:
            multiplier = [1]

        if self.stea_input.ecl_case is None:
            raise ValueError(
                "When adding ecl_profile you must configure an Eclipse case"
            )

        case: EclSum = self.stea_input.ecl_case
        if key not in case:
            raise KeyError(f"No such summary key: {key}")

        if first_year is None:
            start_date = case.start_date
            first_year = start_date.year

        if last_year is None:
            end_date = case.end_date
            last_year = end_date.year

        start_time = datetime.datetime(first_year, 1, 1)
        end_time = datetime.datetime(last_year + 1, 1, 1)
        time_range = case.time_range(start=start_time, end=end_time, interval="1Y")
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

        mult_rangeend = min(len(multiplier), len(data))
        data[:mult_rangeend] = map(
            lambda x, y: x * y, data[:mult_rangeend], multiplier[:mult_rangeend]
        )

        data = [x * global_multiplier for x in data]
        self.add_profile(profile_id, first_year, data)
