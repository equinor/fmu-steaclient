import pytest
import unittest
import json
import os
import subprocess
import datetime
import requests
from requests.exceptions import ConnectionError
from stea import (
    calculate,
    SteaClient,
    SteaRequest,
    SteaProject,
    SteaInput,
    SteaInputKeys,
    SteaKeys,
    SteaResult,
)

from ecl.util.test.ecl_mock import createEclSum
from ecl.util.test import TestAreaContext

test_server = "https://st-w4771.statoil.net"

mock_project = SteaProject(
    {
        SteaKeys.PROFILES: [
            {
                SteaKeys.PROFILE_ID: "ID1",
                SteaKeys.UNIT: "unit1",
                SteaKeys.MULTIPLE: "Mill",
            },
            {SteaKeys.PROFILE_ID: "ID2", SteaKeys.UNIT: "unit2"},
        ],
        SteaKeys.PROJECT_ID: "project-id",
        SteaKeys.PROJECT_VERSION: "100",
    }
)

mock_result = {
    SteaKeys.KEY_VALUES: [
        {SteaKeys.TAX_MODE: SteaKeys.PRETAX, SteaKeys.VALUES: {"NPV": 123}},
        {SteaKeys.TAX_MODE: SteaKeys.CORPORATE, SteaKeys.VALUES: {"NPV": 456}},
    ]
}


class SteaMockClient(object):
    def __init__(self, server):
        pass

    def get_project(self, project_id, project_version, config_date):
        return mock_project


def fopr(days):
    return 1


def fopt(days):
    return days


def fgpt(days):
    if days < 50:
        return days
    else:
        return 100 - days


def create_case(case="CSV", restart_case=None, restart_step=-1, data_start=None):
    length = 1000
    return createEclSum(
        case,
        [
            ("FOPT", None, 0, "SM3"),
            ("FOPR", None, 0, "SM3/DAY"),
            ("FGPT", None, 0, "SM3"),
        ],
        sim_length_days=length,
        num_report_step=10,
        num_mini_step=10,
        data_start=data_start,
        func_table={"FOPT": fopt, "FOPR": fopr, "FGPT": fgpt},
        restart_case=restart_case,
        restart_step=restart_step,
    )


def online():
    try:
        requests.get(test_server, verify=False)
        return True
    except requests.exceptions.ConnectionError:
        return False


@pytest.fixture()
def set_up():
    class Stea:
        def __init__(self):
            self.project_id = 4872
            self.project_version = 3
            self.config_date = datetime.datetime(2018, 6, 26, 11, 0, 0)
            self.fopt_profile_id = "28558281-b82d-42a2-88a5-ba8e3e7d150d"
            self.fopt_profile_id_desc = "FOPT"
            self.test_server = test_server
            if online():
                self.client = SteaClient(self.test_server)
            else:
                self.client = SteaMockClient("test-server")

    yield Stea()


def test_project():
    payload = {
        SteaKeys.PROFILES: [
            {
                SteaKeys.PROFILE_ID: "ID1",
                SteaKeys.UNIT: "unit1",
                SteaKeys.MULTIPLE: "Mill",
            },
            {SteaKeys.PROFILE_ID: "ID2", SteaKeys.UNIT: "unit2"},
        ],
        SteaKeys.PROJECT_ID: "project-id",
        SteaKeys.PROJECT_VERSION: "100",
    }

    project = SteaProject(payload)
    assert project.has_profile("ID1")
    assert not project.has_profile("ID0")

    with pytest.raises(KeyError):
        project.get_profile("XYZ_NO_SUCH_PROFILE")

    with pytest.raises(KeyError):
        project.get_profile_unit("XYZ_NO_SUCH_PROFILE")

    with pytest.raises(KeyError):
        project.get_profile_mult("XYZ_NO_SUCH_PROFILE")

    profile = project.get_profile("ID1")
    assert "unit1" == project.get_profile_unit("ID1")
    assert "Mill" == project.get_profile_mult("ID1")
    assert project.get_profile_mult("ID2") == "1"


def test_config():
    with TestAreaContext("stea_main"):
        with pytest.raises(IOError):
            cnf = SteaInput(["File/does/not/exist"])

        # An invalid YAML file:
        with open("config_file", "w") as f:
            f.write("object:\n")
            f.write("    key: value :\n")

        with pytest.raises(ValueError):
            stea_main = SteaInput(["config_file"])

        with open("config_file", "w") as f:
            f.write("{}: 2018-10-10 12:00:00\n".format(SteaInputKeys.CONFIG_DATE))
            f.write("{}: 1234\n".format(SteaInputKeys.PROJECT_ID))
            f.write("{}: 1\n".format(SteaInputKeys.PROJECT_VERSION))

            f.write("{}: \n".format(SteaInputKeys.ECL_PROFILES))
            f.write("   ID1: \n")
            f.write("      {}: FOPT\n".format(SteaInputKeys.ECL_KEY))
            f.write("   ID2: \n")
            f.write("      {}: FGPT\n".format(SteaInputKeys.ECL_KEY))
            f.write("{}: \n".format(SteaInputKeys.RESULTS))
            f.write("   - npv\n")

        stea_input = SteaInput(["config_file"])
        assert stea_input.config_date == datetime.datetime(2018, 10, 10, 12, 0, 0)
        assert stea_input.project_id == 1234
        assert stea_input.project_version == 1
        assert 2 == len(stea_input.ecl_profiles)
        keys = [key[0] for key in stea_input.ecl_profiles]
        assert "ID1" in keys
        assert "ID2" in keys

        with open("config_file", "w") as f:
            f.write("{}: No-not-a-date".format(SteaInputKeys.CONFIG_DATE))

        with pytest.raises(ValueError):
            stea_main = SteaInput(["config_file"])


def test_input_argv():
    with TestAreaContext("stea_input_argv"):

        with open("config_file", "w") as f:
            f.write("{}: 2018-10-10 12:00:00\n".format(SteaInputKeys.CONFIG_DATE))
            f.write("{}: 1234\n".format(SteaInputKeys.PROJECT_ID))
            f.write("{}: 1\n".format(SteaInputKeys.PROJECT_VERSION))

            f.write("{}: \n".format(SteaInputKeys.ECL_PROFILES))
            f.write("   ID1: \n")
            f.write("      {}: FOPT\n".format(SteaInputKeys.ECL_KEY))
            f.write("   ID2: \n")
            f.write("      {}: FGPT\n".format(SteaInputKeys.ECL_KEY))
            f.write("{}: \n".format(SteaInputKeys.RESULTS))
            f.write("   - npv\n")

        with pytest.raises(IOError):
            stea_input = SteaInput(
                ["config_file", "--{}=CSV".format(SteaInputKeys.ECL_CASE)]
            )

        case = create_case()
        case.fwrite()
        stea_input = SteaInput(
            ["config_file", "--{}=CSV".format(SteaInputKeys.ECL_CASE)]
        )


def test_request1():
    with TestAreaContext("stea_request"):
        with open("config_file", "w") as f:
            f.write("{}: 2018-10-10 12:00:00\n".format(SteaInputKeys.CONFIG_DATE))
            f.write("{}: 1234\n".format(SteaInputKeys.PROJECT_ID))
            f.write("{}: 1\n".format(SteaInputKeys.PROJECT_VERSION))

            f.write("{}: \n".format(SteaInputKeys.ECL_PROFILES))
            f.write("   ID1: \n")
            f.write("      {}: FOPT\n".format(SteaInputKeys.ECL_KEY))
            f.write("   ID2: \n")
            f.write("      {}: FGPT\n".format(SteaInputKeys.ECL_KEY))
            f.write("{}: \n".format(SteaInputKeys.RESULTS))
            f.write("   - npv\n")

        stea_input = SteaInput(["config_file"])
        project = mock_project

        case = create_case()
        case.fwrite()
        request = SteaRequest(stea_input, project)
        with pytest.raises(KeyError):
            request.add_profile("no-such-id", 2018, [0, 1, 2])

        with pytest.raises(ValueError):
            request.add_ecl_profile("ID1", "FOPT")


def test_request2():
    with TestAreaContext("stea_request"):
        case = create_case()
        case.fwrite()
        with open("config_file", "w") as f:
            f.write("{}: 2018-10-10 12:00:00\n".format(SteaInputKeys.CONFIG_DATE))
            f.write("{}: 1234\n".format(SteaInputKeys.PROJECT_ID))
            f.write("{}: 1\n".format(SteaInputKeys.PROJECT_VERSION))

            f.write("{}: \n".format(SteaInputKeys.ECL_PROFILES))
            f.write("   ID1: \n")
            f.write("      {}: FOPT\n".format(SteaInputKeys.ECL_KEY))
            f.write("   ID2: \n")
            f.write("      {}: FGPT\n".format(SteaInputKeys.ECL_KEY))
            f.write("{}: \n".format(SteaInputKeys.RESULTS))
            f.write("   - npv\n")
            f.write("{}: {}\n".format(SteaInputKeys.ECL_CASE, "CSV"))

        stea_input = SteaInput(["config_file"])
        project = mock_project
        request = SteaRequest(stea_input, project)

        with pytest.raises(KeyError):
            request.add_ecl_profile("ID1", "NO-SUCH-KEY")

        with pytest.raises(KeyError):
            request.add_ecl_profile("INVALID-ID", "FOPT")


@pytest.mark.skipif(not online(), reason="Must be on statoil network")
def test_calculate(set_up):
    with TestAreaContext("stea_request"):
        case = create_case()
        case.fwrite()
        with open("config_file", "w") as f:
            f.write("{}: {}\n".format(SteaInputKeys.CONFIG_DATE, set_up.config_date))
            f.write("{}: {}\n".format(SteaInputKeys.PROJECT_ID, set_up.project_id))
            f.write(
                "{}: {}\n".format(SteaInputKeys.PROJECT_VERSION, set_up.project_version)
            )
            f.write("{}: \n".format(SteaInputKeys.ECL_PROFILES))
            f.write("   {}: \n".format(set_up.fopt_profile_id))
            f.write("      {}: FOPT\n".format(SteaInputKeys.ECL_KEY))
            f.write("{}: {}\n".format(SteaInputKeys.SERVER, test_server))
            f.write("{}: \n".format(SteaInputKeys.RESULTS))
            f.write("   - NPV\n")
            f.write("{}: {}\n".format(SteaInputKeys.ECL_CASE, "CSV"))

        stea_input = SteaInput(["config_file"])
        results = calculate(stea_input)
        for res, value in results.results(SteaKeys.CORPORATE).items():
            print("DBG_TEST {}, {}".format(res, value))


def test_results(set_up):
    with TestAreaContext("stea_request"):
        case = create_case()
        case.fwrite()
        with open("config_file", "w") as f:
            f.write("{}: {}\n".format(SteaInputKeys.CONFIG_DATE, set_up.config_date))
            f.write("{}: {}\n".format(SteaInputKeys.PROJECT_ID, set_up.project_id))
            f.write(
                "{}: {}\n".format(SteaInputKeys.PROJECT_VERSION, set_up.project_version)
            )
            f.write("{}: \n".format(SteaInputKeys.ECL_PROFILES))
            f.write("   {}: \n".format(set_up.fopt_profile_id))
            f.write("      {}: FOPT\n".format(SteaInputKeys.ECL_KEY))
            f.write("{}: {}\n".format(SteaInputKeys.SERVER, test_server))
            f.write("{}: \n".format(SteaInputKeys.RESULTS))
            f.write("   - NPV\n")
            f.write("{}: {}\n".format(SteaInputKeys.ECL_CASE, "CSV"))

        stea_input = SteaInput(["config_file"])

    result = SteaResult(mock_result, stea_input)
    with pytest.raises(KeyError):
        res = result.results("NO-SUCH-TAX-MODE")

    res = result.results(SteaKeys.PRETAX)
    assert len(res) == 1
    assert "NPV" in res
    assert res["NPV"] == 123

    res = result.results(SteaKeys.CORPORATE)
    assert len(res) == 1
    assert "NPV" in res
    assert res["NPV"] == 456


@pytest.mark.skipif(not online(), reason="Must be on statoil network")
def test_mult(set_up):
    with TestAreaContext("stea_request"):
        case = create_case()
        case.fwrite()
        with open("config_file", "w") as f:
            f.write("{}: {}\n".format(SteaInputKeys.CONFIG_DATE, set_up.config_date))
            f.write("{}: {}\n".format(SteaInputKeys.PROJECT_ID, set_up.project_id))
            f.write(
                "{}: {}\n".format(SteaInputKeys.PROJECT_VERSION, set_up.project_version)
            )
            f.write("{}: \n".format(SteaInputKeys.ECL_PROFILES))
            f.write("   {}: \n".format(set_up.fopt_profile_id))
            f.write("      {}: FOPT\n".format(SteaInputKeys.ECL_KEY))
            f.write("      {}: [2,1]\n".format(SteaInputKeys.ECL_MULT))
            f.write("{}: {}\n".format(SteaInputKeys.SERVER, test_server))
            f.write("{}: \n".format(SteaInputKeys.RESULTS))
            f.write("   - NPV\n")
            f.write("{}: {}\n".format(SteaInputKeys.ECL_CASE, "CSV"))

        stea_input = SteaInput(["config_file"])
        results = calculate(stea_input)
    res = results.results(SteaKeys.CORPORATE)
    assert len(res) == 1
    assert "NPV" in res
    assert pytest.approx(536.1371967150193, res["NPV"])


@pytest.mark.skipif(not online(), reason="Must be on statoil network")
def test_desc(set_up):
    with TestAreaContext("stea_request"):
        case = create_case()
        case.fwrite()
        with open("config_file", "w") as f:
            f.write("{}: {}\n".format(SteaInputKeys.CONFIG_DATE, set_up.config_date))
            f.write("{}: {}\n".format(SteaInputKeys.PROJECT_ID, set_up.project_id))
            f.write(
                "{}: {}\n".format(SteaInputKeys.PROJECT_VERSION, set_up.project_version)
            )
            f.write("{}: \n".format(SteaInputKeys.ECL_PROFILES))
            f.write("   {}: \n".format(set_up.fopt_profile_id_desc))
            f.write("      {}: FOPT\n".format(SteaInputKeys.ECL_KEY))
            f.write("{}: {}\n".format(SteaInputKeys.SERVER, test_server))
            f.write("{}: \n".format(SteaInputKeys.RESULTS))
            f.write("   - NPV\n")
            f.write("{}: {}\n".format(SteaInputKeys.ECL_CASE, "CSV"))

        stea_input = SteaInput(["config_file"])
        results = calculate(stea_input)
    res = results.results(SteaKeys.CORPORATE)
    assert len(res) == 1
    assert "NPV" in res
    assert pytest.approx(536.1371967150193, res["NPV"])
