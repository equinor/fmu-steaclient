import json

import click
import importlib_resources
from ert.shared.plugins.plugin_manager import hook_implementation
from ert.shared.plugins.plugin_response import plugin_response

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
    As output, for each of the entries in the result section of the
    yaml config file, STEA will create result files
    ex: Res1_0, Res2_0, .. Res#_0"""
    try:
        if ecl_case == "__NONE__":  # This is because ert cant handle optionals
            ecl_case = None
        stea_input = stea.SteaInput(config, ecl_case)
        result = stea.calculate(stea_input)
        for res, value in result.results(stea.SteaKeys.CORPORATE).items():
            with open(f"{res}_0", "w", encoding="utf-8") as ofh:
                ofh.write(f"{value}\n")
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


@hook_implementation
@plugin_response(plugin_name="fmu-steaclient")
def installable_jobs():
    resource_directory_ref = importlib_resources.files("stea") / "fm_stea"
    stea_fm_filename = ""
    with importlib_resources.as_file(resource_directory_ref) as resource_directory:
        stea_fm_filename = str(resource_directory / "STEA_CONFIG")
    return {"STEA": stea_fm_filename}


@hook_implementation
@plugin_response(plugin_name="fmu-steaclient")
def job_documentation(job_name):
    if job_name != "STEA":
        return None

    description = main_entry_point.__doc__
    examples = ""
    category = "modelling.financial"

    return {
        "description": description,
        "examples": examples,
        "category": category,
    }
