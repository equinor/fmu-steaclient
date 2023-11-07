import datetime
import os
import pathlib
from contextlib import ExitStack as does_not_raise

import pytest
import yaml
from resdata.summary import Summary
from resdata.util.test.mock import createSummary

from stea import (
    SteaClient,
    SteaInput,
    SteaInputKeys,
    SteaKeys,
    SteaRequest,
    SteaResult,
    calculate,
    make_request,
)
from stea.stea_request import BARRELS_PR_SM3

# pylint: disable=too-many-arguments

TEST_SERVER = "S723WS007.statoil.net"
TEST_SERVER_URL = f"https://{TEST_SERVER}:1702"


def fopr(_days):
    return 1


def fopt(days):
    return days


def fgpt(days):
    if days < 50:
        return days
    return 100 - days


def create_case(case="CSV", restart_case=None, restart_step=-1, data_start=None):
    length = 1000
    return createSummary(
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
    return os.system(f"ping -c 1 -w2 {TEST_SERVER} >/dev/null 2>&1") == 0


@pytest.fixture(name="set_up")
def fixture_set_up():
    class Stea:
        # pylint: disable=too-few-public-methods
        def __init__(self):
            self.project_id = 4872
            self.project_version = 3
            self.config_date = datetime.datetime(2018, 6, 26, 11, 0, 0)
            self.fopt_profile_id = "28558281-b82d-42a2-88a5-ba8e3e7d150d"
            self.fopt_profile_id_desc = "FOPT"
            self.test_server = TEST_SERVER_URL
            if online():
                self.client = SteaClient(self.test_server)
            else:
                self.client = SteaMockClient("test-server")

    yield Stea()


class SteaMockClient:
    # pylint: disable=too-few-public-methods
    def __init__(self, servername: str):
        pass


def test_project(mock_project):
    assert mock_project.has_profile("ID1")
    assert not mock_project.has_profile("ID0")

    with pytest.raises(KeyError):
        mock_project.get_profile("XYZ_NO_SUCH_PROFILE")

    with pytest.raises(KeyError):
        mock_project.get_profile_unit("XYZ_NO_SUCH_PROFILE")

    with pytest.raises(KeyError):
        mock_project.get_profile_mult("XYZ_NO_SUCH_PROFILE")

    assert "unit1" == mock_project.get_profile_unit("ID1")
    assert "Mill" == mock_project.get_profile_mult("ID1")
    assert mock_project.get_profile_mult("ID2") == "1"


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

    assert ecl_unit  # pylint

    # Mock ECL binary output files:
    case: Summary = create_case()
    case.fwrite()

    stea_input = SteaInput(["config_file"])
    mock_project.profiles["ID1"]["Unit"] = project_unit
    mock_project.profiles["ID1"]["Multiple"] = scale_factor

    request = SteaRequest(stea_input, mock_project)
    # Populate profiles from Summary case:
    request.add_ecl_profile("ID1", "FOPT")

    assert (
        pytest.approx(
            request.request_data["Adjustments"]["Profiles"][0]["Data"]["Data"][0]
        )
        == expected_fopt0
    )


@pytest.mark.parametrize(
    "start_date, start_year, end_year, expected_final_fopt, expectation",
    [
        # FOPR is 1 for all days, so the expected total production in these tests
        # is the day count.
        pytest.param(None, None, None, 990, does_not_raise(), id="no_start_nor_end"),
        pytest.param(
            datetime.date(2010, 1, 1),
            None,
            None,
            990,
            does_not_raise(),
            id="start_same_as_profile",
        ),
        pytest.param(
            datetime.date(2010, 1, 2),
            None,
            None,
            989,
            does_not_raise(),
            id="crop_one_day",
        ),
        pytest.param(
            datetime.date(2010, 7, 1),
            None,
            None,
            990 - 364 / 2 + 1,
            does_not_raise(),
            id="crop_half_year",
        ),
        pytest.param(
            datetime.date(2010, 7, 1),
            None,
            2010,
            364 / 2 + 2,
            does_not_raise(),
            id="crop_half_year_and_remaining",
        ),
        pytest.param(
            datetime.date(2010, 12, 31),
            None,
            2010,
            1,
            does_not_raise(),
            id="crop_to_one_day",
        ),
        pytest.param(
            datetime.date(2010, 1, 3),
            2011,
            None,
            625,
            pytest.raises(
                ValueError,
                match="Do not provide both start_year and start_date",
            ),
            id="ambig_start_year",
        ),
    ],
)
def test_start_date_end_year(
    start_date,
    start_year,
    end_year,
    expected_final_fopt,
    expectation,
    tmpdir,
    mock_project,
):
    os.chdir(tmpdir)
    config = {
        SteaInputKeys.CONFIG_DATE: datetime.datetime(2018, 10, 10, 12, 0, 0),
        SteaInputKeys.PROJECT_ID: 1234,
        SteaInputKeys.PROJECT_VERSION: 1,
        SteaInputKeys.ECL_PROFILES: {
            "ID1": {
                SteaInputKeys.ECL_KEY: "FOPT",
                SteaInputKeys.START_DATE: start_date,
                SteaInputKeys.START_YEAR: start_year,
                SteaInputKeys.END_YEAR: end_year,  # NB: None here gives 'null' in yaml
            }
        },
        SteaInputKeys.RESULTS: ["npv"],
        SteaInputKeys.ECL_CASE: "CSV",
    }
    pathlib.Path("config_file").write_text(yaml.dump(config), encoding="utf-8")
    # Mock ECL binary output files:
    case: Summary = create_case()
    case.fwrite()
    with expectation:
        stea_input = SteaInput(["config_file"])
        request = make_request(stea_input, mock_project)
        assert (
            pytest.approx(
                sum(request.request_data["Adjustments"]["Profiles"][0]["Data"]["Data"])
                * 1e6
            )
            == expected_final_fopt
        )


@pytest.mark.parametrize(
    "start_year, end_year, expected_final_fopt, expectation",
    # NB: start_year is deprecated in favour of start_date
    [
        # The mocked Summary object contains data every tenth date from
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
    case: Summary = create_case()
    case.fwrite()
    with expectation:
        stea_input = SteaInput(["config_file"])
        request = make_request(stea_input, mock_project)
        assert (
            pytest.approx(
                sum(request.request_data["Adjustments"]["Profiles"][0]["Data"]["Data"])
                * 1e6
            )
            == expected_final_fopt
        )


def test_config_not_exists(tmpdir):
    os.chdir(tmpdir)
    with pytest.raises(IOError):
        SteaInput(["File/does/not/exist"])


def test_config_invalid_file(tmpdir):
    os.chdir(tmpdir)
    with open("config_file", "w", encoding="utf-8") as fout:
        fout.write("object:\n")
        fout.write("    key: value :\n")

    with pytest.raises(ValueError):
        SteaInput(["config_file"])


def test_config(tmpdir):
    os.chdir(tmpdir)
    config = {
        SteaInputKeys.CONFIG_DATE: datetime.datetime(2018, 10, 10, 12, 0, 0),
        SteaInputKeys.PROJECT_ID: 1234,
        SteaInputKeys.PROJECT_VERSION: 1,
        SteaInputKeys.ECL_PROFILES: {
            "ID1": {SteaInputKeys.ECL_KEY: "FOPT"},
            "ID2": {SteaInputKeys.ECL_KEY: "FGPT"},
        },
        SteaInputKeys.RESULTS: ["npv"],
    }
    pathlib.Path("config_file").write_text(yaml.dump(config), encoding="utf-8")
    stea_input = SteaInput(["config_file"])
    assert stea_input.config_date == datetime.datetime(2018, 10, 10, 12, 0, 0)
    assert stea_input.project_id == 1234
    assert stea_input.project_version == 1
    assert 2 == len(stea_input.ecl_profiles)
    keys = [key[0] for key in stea_input.ecl_profiles]
    assert "ID1" in keys
    assert "ID2" in keys


def test_config_invalid_date(tmpdir):
    os.chdir(tmpdir)
    with open("config_file", "w", encoding="utf-8") as fout:
        fout.write(f"{SteaInputKeys.CONFIG_DATE}: No-not-a-date")

    with pytest.raises(ValueError):
        SteaInput(["config_file"])


def test_input_argv(tmpdir):
    os.chdir(tmpdir)
    config = {
        SteaInputKeys.CONFIG_DATE: datetime.datetime(2018, 10, 10, 12, 0, 0),
        SteaInputKeys.PROJECT_ID: 1234,
        SteaInputKeys.PROJECT_VERSION: 1,
        SteaInputKeys.ECL_PROFILES: {
            "ID1": {SteaInputKeys.ECL_KEY: "FOPT"},
            "ID2": {SteaInputKeys.ECL_KEY: "FGPT"},
        },
        SteaInputKeys.RESULTS: ["npv"],
    }
    pathlib.Path("config_file").write_text(yaml.dump(config), encoding="utf-8")

    with pytest.raises(IOError):
        SteaInput(["config_file", f"--{SteaInputKeys.ECL_CASE}=CSV"])

    case = create_case()
    case.fwrite()
    SteaInput(["config_file", f"--{SteaInputKeys.ECL_CASE}=CSV"])


def test_request1(tmpdir, mock_project):
    os.chdir(tmpdir)
    config = {
        SteaInputKeys.CONFIG_DATE: datetime.datetime(2018, 10, 10, 12, 0, 0),
        SteaInputKeys.PROJECT_ID: 1234,
        SteaInputKeys.PROJECT_VERSION: 1,
        SteaInputKeys.ECL_PROFILES: {
            "ID1": {SteaInputKeys.ECL_KEY: "FOPT"},
            "ID2": {SteaInputKeys.ECL_KEY: "FGPT"},
        },
        SteaInputKeys.RESULTS: ["npv"],
    }
    pathlib.Path("config_file").write_text(yaml.dump(config), encoding="utf-8")

    stea_input = SteaInput(["config_file"])
    case = create_case()
    case.fwrite()
    request = SteaRequest(stea_input, mock_project)
    with pytest.raises(KeyError, match="Invalid profile id"):
        request.add_profile("no-such-id", 2018, [0, 1, 2])

    with pytest.raises(
        ValueError, match="When adding ecl_profile you must configure an Eclipse case"
    ):
        request.add_ecl_profile("ID1", "FOPT")


def test_request2(tmpdir, mock_project):
    os.chdir(tmpdir)
    case = create_case()
    case.fwrite()
    config = {
        SteaInputKeys.CONFIG_DATE: datetime.datetime(2018, 10, 10, 12, 0, 0),
        SteaInputKeys.PROJECT_ID: 1234,
        SteaInputKeys.PROJECT_VERSION: 1,
        SteaInputKeys.ECL_PROFILES: {
            "ID1": {SteaInputKeys.ECL_KEY: "FOPT"},
            "ID2": {SteaInputKeys.ECL_KEY: "FGPT"},
        },
        SteaInputKeys.RESULTS: ["npv"],
        SteaInputKeys.ECL_CASE: "CSV",
    }
    pathlib.Path("config_file").write_text(yaml.dump(config), encoding="utf-8")

    stea_input = SteaInput(["config_file"])
    request = SteaRequest(stea_input, mock_project)

    with pytest.raises(KeyError):
        request.add_ecl_profile("ID1", "NO-SUCH-KEY")

    with pytest.raises(KeyError):
        request.add_ecl_profile("INVALID-ID", "FOPT")


@pytest.mark.skipif(not online(), reason="Must be on Equinor network")
def test_calculate(set_up, tmpdir):
    os.chdir(tmpdir)
    case = create_case()
    case.fwrite()
    config = {
        SteaInputKeys.CONFIG_DATE: set_up.config_date,
        SteaInputKeys.PROJECT_ID: set_up.project_id,
        SteaInputKeys.PROJECT_VERSION: set_up.project_version,
        SteaInputKeys.ECL_PROFILES: {
            set_up.fopt_profile_id: {SteaInputKeys.ECL_KEY: "FOPT"},
        },
        SteaInputKeys.SERVER: TEST_SERVER_URL,
        SteaInputKeys.RESULTS: ["NPV"],
        SteaInputKeys.ECL_CASE: "CSV",
    }
    pathlib.Path("config_file").write_text(yaml.dump(config), encoding="utf-8")

    stea_input = SteaInput(["config_file"])
    results = calculate(stea_input)
    assert pytest.approx(results.results(SteaKeys.CORPORATE)["NPV"]) == 536.137196


def test_results(set_up, tmpdir, mock_result):
    os.chdir(tmpdir)
    case = create_case()
    case.fwrite()
    config = {
        SteaInputKeys.CONFIG_DATE: set_up.config_date,
        SteaInputKeys.PROJECT_ID: set_up.project_id,
        SteaInputKeys.PROJECT_VERSION: set_up.project_version,
        SteaInputKeys.ECL_PROFILES: {
            set_up.fopt_profile_id: {SteaInputKeys.ECL_KEY: "FOPT"},
        },
        SteaInputKeys.SERVER: TEST_SERVER_URL,
        SteaInputKeys.RESULTS: ["NPV"],
        SteaInputKeys.ECL_CASE: "CSV",
    }
    pathlib.Path("config_file").write_text(yaml.dump(config), encoding="utf-8")

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
def test_mult(set_up, tmpdir):
    os.chdir(tmpdir)
    case = create_case()
    case.fwrite()
    config = {
        SteaInputKeys.CONFIG_DATE: set_up.config_date,
        SteaInputKeys.PROJECT_ID: set_up.project_id,
        SteaInputKeys.PROJECT_VERSION: set_up.project_version,
        SteaInputKeys.ECL_PROFILES: {
            set_up.fopt_profile_id: {
                SteaInputKeys.ECL_KEY: "FOPT",
                SteaInputKeys.ECL_MULT: [2, 1],
            },
        },
        SteaInputKeys.SERVER: TEST_SERVER_URL,
        SteaInputKeys.RESULTS: ["NPV"],
        SteaInputKeys.ECL_CASE: "CSV",
    }
    pathlib.Path("config_file").write_text(yaml.dump(config), encoding="utf-8")

    stea_input = SteaInput(["config_file"])
    results = calculate(stea_input)
    res = results.results(SteaKeys.CORPORATE)
    assert len(res) == 1
    assert "NPV" in res
    assert pytest.approx(res["NPV"]) == 536.1371967150193


@pytest.mark.skipif(not online(), reason="Must be on Equinor network")
def test_desc(set_up, tmpdir):
    os.chdir(tmpdir)
    case = create_case()
    case.fwrite()
    config = {
        SteaInputKeys.CONFIG_DATE: set_up.config_date,
        SteaInputKeys.PROJECT_ID: set_up.project_id,
        SteaInputKeys.PROJECT_VERSION: set_up.project_version,
        SteaInputKeys.ECL_PROFILES: {
            set_up.fopt_profile_id_desc: {SteaInputKeys.ECL_KEY: "FOPT"},
        },
        SteaInputKeys.SERVER: TEST_SERVER_URL,
        SteaInputKeys.RESULTS: ["NPV"],
        SteaInputKeys.ECL_CASE: "CSV",
    }
    pathlib.Path("config_file").write_text(yaml.dump(config), encoding="utf-8")

    stea_input = SteaInput(["config_file"])
    results = calculate(stea_input)
    res = results.results(SteaKeys.CORPORATE)
    assert len(res) == 1
    assert "NPV" in res
    assert pytest.approx(res["NPV"]) == 536.1371967150193
