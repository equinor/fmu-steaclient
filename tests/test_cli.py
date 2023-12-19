import json
import os
import shutil
from unittest import mock

import pytest
import stea
from click.testing import CliRunner
from stea import SteaKeys, SteaResult
from stea.fm_stea.fm_stea import main_entry_point

TEST_STEA_PATH, _ = os.path.split(os.path.abspath(__file__))


@pytest.fixture(name="setup_stea")
def fixture_setup_stea(tmpdir):
    cwd = os.getcwd()
    tmpdir.chdir()
    shutil.copytree(TEST_STEA_PATH, "stea")
    os.chdir(os.path.join("stea"))
    yield
    os.chdir(cwd)


def calculate_patch(stea_input):
    return SteaResult(
        {
            SteaKeys.KEY_VALUES: [
                {SteaKeys.TAX_MODE: SteaKeys.CORPORATE, SteaKeys.VALUES: {"NPV": 30}}
            ]
        },
        stea_input,
    )


@pytest.fixture(autouse=True)
def mock_project(monkeypatch):
    project = {
        SteaKeys.PROJECT_ID: 1,
        SteaKeys.PROJECT_VERSION: 1,
        SteaKeys.PROFILES: [
            {
                SteaKeys.PROFILE_ID: "a_very_long_string",
            },
        ],
    }
    mocked_project = mock.MagicMock(return_value=stea.SteaProject(project))
    monkeypatch.setattr(stea.SteaClient, "get_project", mocked_project)
    yield mocked_project


@pytest.fixture(autouse=True, name="mock_calculate")
def fixture_mock_calculate(monkeypatch):
    mock_stea = mock.MagicMock()
    mock_stea.side_effect = calculate_patch
    monkeypatch.setattr(stea, "calculate", mock_stea)
    yield mock_stea


@pytest.mark.usefixtures("setup_stea")
def test_stea():
    runner = CliRunner()
    result = runner.invoke(main_entry_point, ["-c", "stea_input.yml"])
    assert result.exit_code == 0
    files = os.listdir(os.getcwd())
    # the resulting file i.e. key is defined in the input config file: stea_input.yml
    assert "NPV_0" in files
    assert "stea_response.json" in files


@pytest.mark.usefixtures("setup_stea")
def test_stea_response():
    expected_result = {
        "response": [{"TaxMode": "Corporate", "Values": {"NPV": 30}}],
        "profiles": {"a_very_long_string": {"Id": "a_very_long_string"}},
    }
    runner = CliRunner()
    result = runner.invoke(main_entry_point, ["-c", "stea_input.yml"])
    assert result.exit_code == 0
    with open("stea_response.json", "r", encoding="utf-8") as fin:
        result = json.load(fin)
    assert result == expected_result


@pytest.mark.usefixtures("setup_stea")
def test_stea_ecl_case_overwrite():
    """
    We want to verify that the ecl_case argument is properly forwarded to stea, but
    there is no ecl_case, so we just assert that we fail with our custom file missing
    """
    runner = CliRunner()
    result = runner.invoke(
        main_entry_point, ["-c", "stea_input.yml", "--ecl_case", "custom_ecl_case"]
    )
    assert result.exit_code == 1
    assert (
        result.output
        == "Error: Failed to create summary instance from argument:custom_ecl_case\n"
    )


@pytest.mark.usefixtures("setup_stea")
def test_stea_default_ert_args():
    """
    We want to verify that the default ert args are correct, so basically that the
    script does not fail.
    """
    runner = CliRunner()
    result = runner.invoke(
        main_entry_point,
        [
            "-c",
            "stea_input.yml",
            "-e",
            "__NONE__",
            "-r",
            "stea_response.json",
        ],
    )
    assert result.exit_code == 0
