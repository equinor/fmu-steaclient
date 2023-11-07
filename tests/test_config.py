import copy
from datetime import datetime

import pytest
import yaml

from stea import stea_input


@pytest.fixture()
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
def test_minimal_config(ecl_case, mocker, monkeypatch):
    valid_config = {
        "config_date": datetime(2018, 10, 10, 12, 0),
        "project_id": 1234,
        "project_version": 1,
        "ecl_profiles": {"ID1": {"ecl_key": "FOPT"}},
        "results": ["npv"],
    }

    args = mocker.Mock()

    summary = mocker.Mock()
    monkeypatch.setattr(stea_input, "Summary", summary)

    args.config_file = "config_file.yml"
    args.ecl_case = ecl_case
    argv = mocker.Mock(return_value=args)
    monkeypatch.setattr(stea_input, "parse_args", argv)

    with open("config_file.yml", "w", encoding="utf-8") as fout:
        yaml.dump(valid_config, fout)

    stea_input.SteaInput("something")

    assert argv.called_once()

    if ecl_case:
        assert summary.called_once_with(ecl_case)


@pytest.mark.usefixtures("use_tmpdir")
@pytest.mark.parametrize(
    "required_key",
    ["config_date", "project_id", "project_version", "ecl_profiles", "results"],
)
def test_invalid_config(required_key, mocker, monkeypatch):
    valid_dict = {
        "config_date": datetime(2018, 10, 10, 12, 0),
        "project_id": 1234,
        "project_version": 1,
        "ecl_profiles": {"ID1": {"ecl_key": "FOPT"}},
        "results": ["npv"],
    }
    invalid_dict = remove_key(valid_dict, required_key)
    args = mocker.Mock()

    summary = mocker.Mock()
    monkeypatch.setattr(stea_input, "Summary", summary)

    args.config_file = "config_file.yml"
    args.ecl_case = None
    argv = mocker.Mock(return_value=args)
    monkeypatch.setattr(stea_input, "parse_args", argv)

    with open("config_file.yml", "w", encoding="utf-8") as fout:
        yaml.dump(invalid_dict, fout)

    with pytest.raises(ValueError):
        stea_input.SteaInput("something")

    assert argv.called_once()
