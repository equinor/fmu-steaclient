try:
    from .version import version as __version__
except ImportError:
    __version__ = "0.0.0"

from .stea_client import SteaClient
from .stea_config import SteaConfig  # noqa
from .stea_input import SteaInput  # noqa
from .stea_keys import SteaInputKeys, SteaKeys  # noqa
from .stea_project import SteaProject  # noqa
from .stea_request import SteaRequest
from .stea_result import SteaResult


def make_request(stea_input: SteaInput, project: SteaProject) -> SteaRequest:
    request = SteaRequest(stea_input, project)

    for profile_id, profile_data in stea_input.ecl_profiles.items():
        if profile_id not in project.profiles:
            profile_list = [
                k
                for k, v in project.profiles.items()
                if v.get(SteaInputKeys.PROFILE_KEY) == profile_id
            ]
        else:
            profile_list = [profile_id]
        if len(profile_list) > 0:
            ecl_key = profile_data.ecl_key
            mult = profile_data.mult
            glob_mult = profile_data.glob_mult
            for pid in profile_list:
                if mult is None:
                    mult = [1]
                if glob_mult is None:
                    glob_mult = 1.0
                request.add_ecl_profile(
                    pid,
                    ecl_key,
                    start_date=profile_data.start_date,
                    end_year=profile_data.end_year,
                    multiplier=mult,
                    global_multiplier=glob_mult,
                )

    for profile_id, profile_data in stea_input.profiles.items():
        if profile_id not in project.profiles:
            profile_list = [
                k
                for k, v in project.profiles.items()
                if v.get(SteaInputKeys.PROFILE_KEY) == profile_id
            ]
        else:
            profile_list = [profile_id]
        if len(profile_list) > 0:
            start_year = profile_data.start_year
            data = profile_data.data
            for pid in profile_list:
                request.add_profile(pid, start_year, data)
    return request


def calculate(stea_input):
    client = SteaClient(stea_input.stea_server)
    project = client.get_project(
        stea_input.project_id, stea_input.project_version, stea_input.config_date
    )
    request = make_request(stea_input, project)
    return SteaResult(client.calculate(request), stea_input)
