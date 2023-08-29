import json

import requests
import urllib3
from requests import RequestException
from requests.exceptions import HTTPError

from .stea_project import SteaProject


def date_string(timestamp):
    return timestamp.strftime("%Y-%m-%dT%H:%M:%S")


class SteaClient:
    def __init__(self, server):
        # Skip certificate verification as the default https_proxy is set to point to
        # port 80 on-premise, making this warning hard to avoid by other means.
        # pylint: disable=no-member
        # https://github.com/PyCQA/pylint/issues/4584
        requests.packages.urllib3.disable_warnings(
            category=urllib3.exceptions.InsecureRequestWarning
        )

        self.server = server

    def get_project(self, project_id, project_version, config_date):
        url = (
            f"{self.server}/api/v1/Alternative/{project_id}/{project_version}/"
            f"summary?ConfigurationDate={date_string(config_date)}"
        )
        try:
            response = requests.get(url, verify=False, timeout=60)

            # pylint: disable=no-member
            if not response.status_code == requests.codes.ok:
                raise HTTPError(
                    f"Could not GET from: {url}  "
                    f"status: {response.status_code} msg: {response.text}"
                )
        except RequestException as error:
            raise RuntimeError(f"HTTP GET form {url} failed") from error

        # Do not really understand this: When pasting the url in the browser
        # field an XML document comes up, but the returned text seems to be a
        # json formatted string. The interface might offer several formats, and
        # the requests library and the browser might have different default
        # preferences.
        project = json.loads(response.text)
        return SteaProject(project)

    def calculate(self, request):
        # self._validate_request()
        url = f"{self.server}/api/v1/Calculate/"
        try:
            response = requests.post(url, json=request.data(), verify=False, timeout=60)
            # pylint: disable=no-member
            if not response.status_code == requests.codes.ok:
                raise HTTPError(
                    f"Could not post to: {url}  status: {response.status_code} "
                    f"msg: {response.text}"
                )
        except RequestException as error:
            raise RuntimeError(f"HTTP POST to {url} failed") from error

        return json.loads(response.text)
