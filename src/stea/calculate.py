from .make_request import make_request
from .stea_client import SteaClient
from .stea_config import SteaConfig  # noqa: F401
from .stea_keys import SteaInputKeys, SteaKeys  # noqa: F401
from .stea_result import SteaResult


def calculate(stea_input):
    client = SteaClient(stea_input.stea_server)
    project = client.get_project(
        stea_input.project_id, stea_input.project_version, stea_input.config_date
    )
    request = make_request(stea_input, project)
    return SteaResult(client.calculate(request), stea_input)
