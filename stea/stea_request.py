import datetime
import types
from .stea_keys import SteaKeys

def date_string(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


class SteaRequest(object):
    units = {"Bbl" : {"SM3" : 1.0/6.2898 },
             "Sm3" : {"SM3" : 1.0}}

    scale_factors = {"1"        : 1.0,
                     "Mill"     : 1.0e-6,
                     "1000 Mill": 1.0e-9}


    def __init__(self, stea_input, project):
        self.stea_input = stea_input
        self.project = project
        self.request_data = { SteaKeys.PROJECT_ID      : project.project_id,
                              SteaKeys.PROJECT_VERSION : project.project_version,
                              SteaKeys.CONFIG_DATE     : date_string(stea_input.config_date),
                              SteaKeys.RESULTS         : stea_input.results,
                              SteaKeys.ADJUSTMENTS     : {
                                  SteaKeys.PROFILES : [
                                  ]
                              }
        }


    def add_profile(self, profile_id, start_year, data):
        if not self.project.has_profile(profile_id):
            raise KeyError("Invalid profile id:{} for this project".format(profile_id))

        profile_data = {SteaKeys.PROFILE_ID : profile_id,
                        SteaKeys.DATA_OUTER : {
                            SteaKeys.DATA_INNER : data,
                            SteaKeys.START_YEAR : start_year }}

        self.request_data[SteaKeys.ADJUSTMENTS][SteaKeys.PROFILES].append(profile_data)


    def data(self):
        return self.request_data


    def add_ecl_profile(self, profile_id, key, first_year=None, last_year=None, multiplier=None):
        if self.stea_input.ecl_case is None:
            raise ValueError("When adding ecl_profile you must configure an Eclipse case")

        case = self.stea_input.ecl_case
        if key not in case:
            raise KeyError("No such summary key: {}".format(key))

        if first_year is None:
            start_date = case.start_date
            first_year = start_date.year

        if last_year is None:
            end_date = case.end_date
            last_year = end_date.year

        if multiplier is None:
            multiplier = 1.0

        start_time = datetime.datetime(first_year, 1, 1)
        end_time = datetime.datetime(last_year + 1, 1,1)
        time_range = case.time_range(start=start_time, end=end_time, interval="1Y")
        ecl_unit = case.unit(key)

        unit = self.project.get_profile_unit(profile_id)
        mult = self.project.get_profile_mult(profile_id)
        unit_conversion = self.units[unit][ecl_unit] * self.scale_factors[mult]
        data = list(case.blocked_production(key, time_range) * unit_conversion)
        if isinstance(multiplier, types.ListType):
          ni=min(len(multiplier),len(data))
          data[:ni]=map(lambda x,y:x*y,data[:ni],multiplier[:ni])
        else:
          data = [x*multiplier for x in data]
        self.add_profile(profile_id, first_year, data)

