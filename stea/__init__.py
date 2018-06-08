"""
Small client which can call the Stea web service to perform economic analysis.

Stea is a Statoil application to perform economic analysis. The application is
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
    __version__ = '0.0.0'


from .stea_keys import SteaKeys, SteaInputKeys
from .stea_client import SteaClient
from .stea_project import SteaProject
from .stea_request import SteaRequest
from .stea_input import SteaInput
from .stea_result import SteaResult


def calculate(stea_input):
    client = SteaClient(stea_input.server)
    project = client.get_project(stea_input.project_id,
                                 stea_input.project_version,
                                 stea_input.config_date)
    request = SteaRequest(stea_input, project)

    for profile_id, profile_data in stea_input.ecl_profiles.iteritems():
        ecl_key = profile_data[SteaInputKeys.ECL_KEY]
        start_year = profile_data.get(SteaInputKeys.START_YEAR)
        end_year = profile_data.get(SteaInputKeys.END_YEAR)

        request.add_ecl_profile(profile_id, ecl_key, first_year=start_year, last_year=end_year)


    for profile_id, profile_data in stea_input.profiles.iteritems():
        start_year = profile_data.get(SteaInputKeys.START_YEAR)
        data = profile_data.get(SteaInputKets.DATA)

        request.add_profile(profile_id, start_year, data)

    return SteaResult(client.calculate(request), stea_input)

