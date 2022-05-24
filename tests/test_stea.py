import datetime
import os
import pathlib
from contextlib import ExitStack as does_not_raise

import pytest
import requests
import urllib3
import yaml
from ecl.summary import EclSum
from ecl.util.test import TestAreaContext
from ecl.util.test.ecl_mock import createEclSum

from stea import (
    SteaClient,
    SteaInput,
    SteaInputKeys,
    SteaKeys,
    SteaProject,
    SteaRequest,
    SteaResult,
    calculate,
    make_request,
)
from stea.stea_request import BARRELS_PR_SM3

test_server = "https://st-w4771.statoil.net"


@pytest.fixture
def mock_project():
    return SteaProject(
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
        return mock_project()


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
        # pylint: disable=no-member
        # https://github.com/PyCQA/pylint/issues/4584
        requests.packages.urllib3.disable_warnings(
            category=urllib3.exceptions.InsecureRequestWarning
        )
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

    assert "unit1" == project.get_profile_unit("ID1")
    assert "Mill" == project.get_profile_mult("ID1")
    assert project.get_profile_mult("ID2") == "1"


@pytest.mark.parametrize(
    "ecl_unit, project_unit, scale_factor, expected_fopt0",
    [
        ("SM3", "Sm3", "Mill", fopr(0) * 365 / 1e6),
        ("SM3", "Bbl", "Mill", fopr(0) * 365 / 1e6 * BARRELS_PR_SM3),
        ("bogus", "Sm3", "Mill", fopr(0) * 365 / 1e6),
        ("SM3", "bogus", "Mill", fopr(0) * 365 / 1e6),
        ("SM3", "Sm3", "1", fopr(0) * 365),
        ("Bogus", "Sm3", "1", fopr(0) * 365),
        ("SM3", "Bbl", "1", fopr(0) * 365 * BARRELS_PR_SM3),
        ("SM3", "Sm3", "1000 Mill", fopr(0) * 365 / 1e9),
        ("SM3", "Bbl", "1000 Mill", fopr(0) * 365 / 1e9 * BARRELS_PR_SM3),
    ],
)
def test_units_and_scale_factor(
    tmpdir, ecl_unit, project_unit, scale_factor, expected_fopt0, mock_project
):
    """STEA-project units in bbl, Eclipse units in sm3"""
    os.chdir(tmpdir)
    config = {
        SteaInputKeys.CONFIG_DATE: datetime.datetime(2018, 10, 10, 12, 0, 0),
        SteaInputKeys.PROJECT_ID: 1234,
        SteaInputKeys.PROJECT_VERSION: 1,
        SteaInputKeys.ECL_PROFILES: {
            "ID1": {SteaInputKeys.ECL_KEY: "FOPT"},
            # (units are not to be specified here)
        },
        SteaInputKeys.RESULTS: ["npv"],
        SteaInputKeys.ECL_CASE: "CSV",
    }
    pathlib.Path("config_file").write_text(yaml.dump(config), encoding="utf-8")

    # Mock ECL binary output files:
    case: EclSum = create_case()
    case.fwrite()

    stea_input = SteaInput(["config_file"])
    mock_project.profiles["ID1"]["Unit"] = project_unit
    mock_project.profiles["ID1"]["Multiple"] = scale_factor

    request = SteaRequest(stea_input, mock_project)
    # Populate profiles from EclSum case:
    request.add_ecl_profile("ID1", "FOPT")

    assert (
        pytest.approx(
            request.request_data["Adjustments"]["Profiles"][0]["Data"]["Data"][0]
        )
        == expected_fopt0
    )


@pytest.mark.parametrize(
    "start_year, end_year, expected_final_fopt, expectation",
    [
        # The mocked EclSum object contains data every tenth date from
        # 2010-01-01 and onwards for 1000 days. The 990th dah is 2012-09-17.
        # There is no data for the 1000th day, so when summing FOPT, the FOPR
        # for the last entry is not accounted for, thus we end with 990 as the
        # final FOPT. FOPR is 1 for all days.
        pytest.param(None, None, 990, does_not_raise(), id="no_start_nor_end"),
        pytest.param(2010, None, 990, does_not_raise(), id="start_same_as_profile"),
        pytest.param(2000, 2013, 990, does_not_raise(), id="start_prior_to_profile"),
        pytest.param(2010, 2013, 990, does_not_raise(), id="start_end_same_as_profile"),
        pytest.param(2011, 2013, 990 - 365, does_not_raise(), id="crop_at_start"),
        pytest.param(
            2012, 2013, 990 - 2 * 365, does_not_raise(), id="crop_more_at_start"
        ),
        pytest.param(
            2013,
            2013,
            None,
            pytest.raises(ValueError, match="Invalid time interval start after end"),
            id="start_after_profile",
        ),
        pytest.param(2010, 2012, 990, does_not_raise(), id="end_year_is_inclusive"),
        pytest.param(2010, 2011, 2 * 365, does_not_raise(), id="crop_from_end"),
        pytest.param(2010, 2010, 365, does_not_raise(), id="crop_more_from_end"),
        pytest.param(
            2010,
            2009,
            None,
            pytest.raises(ValueError, match="Invalid time interval start after end"),
            id="end_before_profile",
        ),
    ],
)
def test_start_year_end_year(
    start_year, end_year, expected_final_fopt, expectation, tmpdir, mock_project
):
    os.chdir(tmpdir)
    config = {
        SteaInputKeys.CONFIG_DATE: datetime.datetime(2018, 10, 10, 12, 0, 0),
        SteaInputKeys.PROJECT_ID: 1234,
        SteaInputKeys.PROJECT_VERSION: 1,
        SteaInputKeys.ECL_PROFILES: {
            "ID1": {
                SteaInputKeys.ECL_KEY: "FOPT",
                SteaInputKeys.START_YEAR: start_year,
                SteaInputKeys.END_YEAR: end_year,  # NB: None here gives 'null' in yaml
            }
        },
        SteaInputKeys.RESULTS: ["npv"],
        SteaInputKeys.ECL_CASE: "CSV",
    }
    pathlib.Path("config_file").write_text(yaml.dump(config), encoding="utf-8")
    # Mock ECL binary output files:
    case: EclSum = create_case()
    case.fwrite()
    stea_input = SteaInput(["config_file"])
    with expectation:
        request = make_request(stea_input, mock_project)
        assert (
            pytest.approx(
                sum(request.request_data["Adjustments"]["Profiles"][0]["Data"]["Data"])
                * 1e6
            )
            == expected_final_fopt
        )


def test_config():
    with TestAreaContext("stea_main"):
        with pytest.raises(IOError):
            SteaInput(["File/does/not/exist"])

        # An invalid YAML file:
        with open("config_file", "w") as f:
            f.write("object:\n")
            f.write("    key: value :\n")

        with pytest.raises(ValueError):
            SteaInput(["config_file"])

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
            SteaInput(["config_file"])


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
            SteaInput(["config_file", "--{}=CSV".format(SteaInputKeys.ECL_CASE)])

        case = create_case()
        case.fwrite()
        SteaInput(["config_file", "--{}=CSV".format(SteaInputKeys.ECL_CASE)])


def test_request1(mock_project):
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

        case = create_case()
        case.fwrite()
        request = SteaRequest(stea_input, mock_project)
        with pytest.raises(KeyError):
            request.add_profile("no-such-id", 2018, [0, 1, 2])

        with pytest.raises(ValueError):
            request.add_ecl_profile("ID1", "FOPT")


def test_request2(mock_project):
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
        request = SteaRequest(stea_input, mock_project)

        with pytest.raises(KeyError):
            request.add_ecl_profile("ID1", "NO-SUCH-KEY")

        with pytest.raises(KeyError):
            request.add_ecl_profile("INVALID-ID", "FOPT")


@pytest.mark.skipif(not online(), reason="Must be on Equinor network")
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


@pytest.mark.skipif(not online(), reason="Must be on Equinor network")
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
    assert pytest.approx(res["NPV"]) == 536.1371967150193


@pytest.mark.skipif(not online(), reason="Must be on Equinor network")
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
    assert pytest.approx(res["NPV"]) == 536.1371967150193
