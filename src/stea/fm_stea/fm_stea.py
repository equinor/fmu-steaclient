import json
import shutil
from pathlib import Path

import click
from ert import (
    ForwardModelStepDocumentation,
    ForwardModelStepPlugin,
)
from ert import (
    plugin as ert_plugin,
)

import stea


@click.command()
@click.option(
    "--config",
    "-c",
    help="STEA config file, yaml format required",
    type=click.Path(exists=True),
    required=True,
)
@click.option(
    "--ecl_case",
    "-e",
    default=None,
    help="Case name, will overwrite the value in the config if provided",
)
@click.option(
    "--response_file",
    "-r",
    default="stea_response.json",
    help="STEA response, json format",
    type=click.Path(exists=False),
)
def main_entry_point(config, ecl_case, response_file):
    """STEA is a powerful economic analysis tool used for complex economic
    analysis and portfolio optimization. STEA helps you analyze single
    projects, large and small portfolios and complex decision trees.

    As output STEA will create result files named according to
    the results specified in the configuration,
    ex: NPV_0, IRR_0, CEI_0, BreakEven_0.

    See https://github.com/equinor/fmu-steaclient for documentation of the
    yaml config file.
    """
    try:  # noqa: PLW0717
        if ecl_case == "__NONE__":  # This is because ert can't handle optionals
            ecl_case = None
        stea_input = stea.SteaInput(config, ecl_case)
        result = stea.calculate(stea_input)
        for res, value in result.results(stea.SteaKeys.CORPORATE).items():
            Path(f"{res}_0").write_text(f"{value}\n", encoding="utf-8")
        profiles = _get_profiles(
            stea_input.stea_server,
            stea_input.project_id,
            stea_input.project_version,
            stea_input.config_date,
        )
        full_response = _build_full_response(
            result.data[stea.SteaKeys.KEY_VALUES], profiles
        )
        with open(response_file, "w", encoding="utf-8") as fout:
            json.dump(full_response, fout, indent=4)
    except Exception as err:
        raise click.exceptions.ClickException(str(err)) from err


def _get_profiles(server, project_id, project_version, config_date):
    client = stea.SteaClient(server)
    project = client.get_project(project_id, project_version, config_date)
    return project.profiles


def _build_full_response(result, profiles):
    return {"response": result, "profiles": profiles}


class FmuSteaclient(ForwardModelStepPlugin):
    def __init__(self) -> None:
        super().__init__(
            name="STEA",
            command=[
                shutil.which("fmu_steaclient") or "fmu_steaclient",
                "--config",
                "<CONFIG>",
                "--response_file",
                "<RESPONSE_FILE>",
                "--ecl_case",
                "<ECL_CASE>",
            ],
            default_mapping={
                "<RESPONSE_FILE>": "stea_response.json",
                "<ECL_CASE>": "__NONE__",
            },
        )

    @staticmethod
    def documentation() -> ForwardModelStepDocumentation:
        return ForwardModelStepDocumentation(
            description=str(main_entry_point.__doc__),
            category="modelling.financial",
            examples="",
        )


@ert_plugin(name="stea")
def installable_forward_model_steps() -> list[type[ForwardModelStepPlugin]]:
    return [FmuSteaclient]
