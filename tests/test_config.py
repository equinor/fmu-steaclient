import copy
from datetime import date, datetime
from unittest.mock import MagicMock

import pytest
import yaml

from stea import SteaConfig, stea_input


@pytest.fixture
def use_tmpdir(tmpdir):
    with tmpdir.as_cwd():
        yield


def remove_key(orig_dict, key):
    invalid_dict = copy.copy(orig_dict)
    invalid_dict.pop(key)
    return invalid_dict


@pytest.mark.usefixtures("use_tmpdir")
@pytest.mark.parametrize(
    "ecl_case",
    [
        "some_ecl_case_name",
        None,
    ],
)
@pytest.mark.parametrize(
    "config_date", [date(2018, 10, 10), datetime(2018, 10, 10, 12, 0)]
)
def test_minimal_config(ecl_case, monkeypatch, config_date):
    valid_config = {
        "config_date": config_date,
        "project_id": 1234,
        "project_version": 1,
        "ecl_profiles": {"ID1": {"ecl_key": "FOPT"}},
        "results": ["npv"],
    }

    summary = MagicMock()
    monkeypatch.setattr(stea_input, "Summary", summary)

    with open("config_file.yml", "w", encoding="utf-8") as fout:
        yaml.dump(valid_config, fout)

    stea_input.SteaInput("config_file.yml", ecl_case)

    if ecl_case:
        summary.assert_called_once_with(ecl_case)


@pytest.mark.usefixtures("use_tmpdir")
@pytest.mark.parametrize(
    "required_key",
    ["config_date", "project_id", "project_version", "ecl_profiles", "results"],
)
def test_invalid_config(required_key, monkeypatch):
    valid_dict = {
        "config_date": datetime(2018, 10, 10, 12, 0),
        "project_id": 1234,
        "project_version": 1,
        "ecl_profiles": {"ID1": {"ecl_key": "FOPT"}},
        "results": ["npv"],
    }
    invalid_dict = remove_key(valid_dict, required_key)

    summary = MagicMock()
    monkeypatch.setattr(stea_input, "Summary", summary)

    with open("config_file.yml", "w", encoding="utf-8") as fout:
        yaml.dump(invalid_dict, fout)

    with pytest.raises(ValueError, match="Could not load config file"):
        stea_input.SteaInput("config_file.yml", None)


def test_deprecated_config_keys():
    valid_config = {
        "config-date": datetime(2018, 10, 10, 12, 0),
        "project-id": 1234,
        "project-version": 1,
        "ecl-profiles": {"ID1": {"ecl_key": "FOPT"}},
        "results": ["npv"],
    }
    SteaConfig(**valid_config)


@pytest.mark.parametrize("ecl_case", ["ecl-case", "ecl_case"])
def test_overwrite_ecl_case(tmp_path, monkeypatch, ecl_case):
    monkeypatch.chdir(tmp_path)
    valid_config = {
        "config-date": datetime(2018, 10, 10, 12, 0),
        "project-id": 1234,
        "project-version": 1,
        "ecl-profiles": {"ID1": {"ecl_key": "FOPT"}},
        "results": ["npv"],
        ecl_case: "case",
    }
    summary = MagicMock()
    monkeypatch.setattr(stea_input, "Summary", summary)

    with open("config_file.yml", "w", encoding="utf-8") as fout:
        yaml.dump(valid_config, fout)
    config = stea_input.SteaInput("config_file.yml", "another_case").config
    assert config.ecl_case == "another_case"
