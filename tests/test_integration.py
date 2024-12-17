"""Test STEA forward model towards the HTTP STEA library"""

import subprocess
from datetime import datetime
from pathlib import Path

import pytest
from resdata.summary import Summary

from stea import SteaKeys

BASE_STEA_CONFIG = """
project-id: 56892
project-version: 1
config-date: 2018-11-01 00:00:00
ecl-profiles:
  FOPT:
    ecl-key: FOPT
ecl-case: {}
results:
  - NPV
"""

BASE_ERT_CONFIG = """
RUNPATH realization-%d/iter-%d
ECLBASE {ecl_base}
QUEUE_SYSTEM LOCAL
NUM_REALIZATIONS 1

FORWARD_MODEL STEA(<CONFIG>=<CONFIG_PATH>/stea_conf.yml{fm_options})
"""


@pytest.fixture
def setup_tmpdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    summary = Summary.writer("NORNE_ATW2013", datetime(2000, 1, 1), 10, 10, 10)

    summary.add_variable("FOPT", unit="SM3")
    summary.add_variable("FOPR", unit="SM3/DAY")
    mini_step_count = 10
    for mini_step in range(mini_step_count):
        t_step = summary.addTStep(1, sim_days=mini_step_count + mini_step)
        t_step["FOPR"] = 1
    summary.fwrite()


@pytest.mark.usefixtures("setup_tmpdir")
@pytest.mark.parametrize(
    "ecl_case, ecl_base, fm_options",
    [
        ("NORNE_ATW2013", "random_eclbase", ""),
        ("a_random_ecl_case", "<CONFIG_PATH>/NORNE_ATW2013", ",<ECL_CASE>=<ECLBASE>"),
    ],
)
def test_stea_fm_single_real(httpserver, ecl_case, ecl_base, fm_options):
    httpserver.expect_request(
        "/foobar/api/v1/Alternative/56892/1/summary",
        query_string="ConfigurationDate=2018-11-01T00:00:00",
    ).respond_with_json(
        {
            "AlternativeId": 1,
            "AlternativeVersion": 1,
            "Profiles": [{"Id": "FOPT", "Unit": "SM3"}],
        }
    )
    httpserver.expect_request(
        "/foobar/api/v1/Calculate/", method="POST"
    ).respond_with_json(
        {
            SteaKeys.KEY_VALUES: [
                {SteaKeys.TAX_MODE: SteaKeys.CORPORATE, SteaKeys.VALUES: {"NPV": 30}}
            ]
        },
    )
    server = httpserver.url_for("/foobar")
    # Mock a forward model configuration file
    Path("stea_conf.yml").write_text(
        BASE_STEA_CONFIG.format((Path() / ecl_case).absolute())
        + f"\nstea_server: {server}",
        encoding="utf-8",
    )

    # Write an ERT config file
    Path("config.ert").write_text(
        BASE_ERT_CONFIG.format(ecl_base=ecl_base, fm_options=fm_options),
        encoding="utf-8",
    )

    subprocess.check_call(["ert", "test_run", "config.ert", "--verbose"])

    assert Path("realization-0/iter-0/NPV_0").read_text(encoding="utf-8")[0:3] == "30\n"
    assert Path("realization-0/iter-0/stea_response.json").exists()
