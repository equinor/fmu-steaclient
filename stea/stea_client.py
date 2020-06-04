import requests
import json
from requests import RequestException
from requests.exceptions import HTTPError

from .stea_project import SteaProject


def date_string(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


class SteaClient(object):
    def __init__(self, server):
        self.server = server

    def get_project(self, project_id, project_version, config_date):
        url = "{server}/api/v1/Alternative/{project_id}/{project_version}/summary?ConfigurationDate={config_date}".format(
            server=self.server,
            project_id=project_id,
            project_version=project_version,
            config_date=date_string(config_date),
        )
        try:
            response = requests.get(url, verify=False)
            if not response.status_code == requests.codes.ok:
                raise HTTPError(
                    "Could not GET from: {url}  status: {status} msg: {text}".format(
                        url=url, status=response.status_code, text=response.text
                    )
                )
        except RequestException as e:
            raise RuntimeError(
                "HTTP GET form {url} failed: {error}]".format(url=url, error=str(e))
            )

        # Do not really understand this: When pasting the url in the browser
        # field an XML document comes up, but the returned text seems to be a
        # json formatted string. The interface might offer several formats, and
        # the requests library and the browser might have different default
        # preferences.
        project = json.loads(response.text)
        return SteaProject(project)

    def calculate(self, request):
        # self._validate_request()
        url = "{}/api/v1/Calculate/".format(self.server)
        try:
            response = requests.post(url, json=request.data(), verify=False)
            if not response.status_code == requests.codes.ok:
                raise HTTPError(
                    "Could not post to: {url}  status: {status} msg: {text}".format(
                        url=url, status=response.status_code, text=response.text
                    )
                )
        except RequestException as e:
            raise RuntimeError(
                "HTTP POST to {url} failed: {error}]".format(url=url, error=str(e))
            )

        return json.loads(response.text)
