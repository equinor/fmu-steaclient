"""
Small client which can call the Stea web service to perform economic analysis.

Stea is an Equinor application to perform economic analysis. The application is
an interactive windows application. In addition to the desktop application
there is a server solution for storage of projects and calculations service.
The purpose of this Python package is to invoke a Stea economic analysis on the
server.

This client only gives access to a very limited amount of the Stea
capabilities. The workflow for using this client is as follows:

 1. A Stea project is defined using the Stea desktop application. This project
    must be 100% complete.

 2. The profiles - i.e. yearly cost and income for the project can be adjusted,
    the principle for this client is to post adjusted profiles to the server.

This package consists of the following classes:

  SteaKeys: This a set of string constants which are used in the schema for
     HTTP communication with the Stea server.

  SteaInput: This is a small configuration object internalizing the input to
     the Stea calculations. The input typically includes:

       o Id of the Stea project, this is given both as an ID and a version.

       o If of the profiles which can should be adjusted, and the eclipse key
         used to fetch them or alternatively the values themselves.

     The input is currrently given as a YAML formatted file.

  SteaInputKeys: A set of string constants used in the YAML input file.

  SteaClient: A small class with a method to POST results to the Stea server
     and a method to GET project data from the server.

  SteaProject: Some information from the real stea project is needed to create
     the calculation request. This information is internalized in the
     SteaProject class. The project is created by doing a http GET from the server.

  SteaRequest: The payload passed in the HTTP POST request is assembled in a
     SteaRequest object.

  SteaResult: Small wrapping of the return value from the stea calcualtion.

"""

try:
    from .version import version as __version__
except ImportError:
    __version__ = "0.0.0"

from .stea_client import SteaClient
from .stea_config import _build_schema  # noqa
from .stea_input import SteaInput  # noqa
from .stea_keys import SteaInputKeys, SteaKeys  # noqa
from .stea_project import SteaProject  # noqa
from .stea_request import SteaRequest
from .stea_result import SteaResult


def make_request(stea_input: SteaInput, project: SteaProject) -> SteaRequest:
    request = SteaRequest(stea_input, project)

    for profile_id, profile_data in stea_input.ecl_profiles:
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

    for profile_id, profile_data in stea_input.profiles:
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
