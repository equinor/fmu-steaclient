import json

from ert.shared.plugins.plugin_manager import hook_implementation
from ert.shared.plugins.plugin_response import plugin_response
from pkg_resources import resource_filename

import stea


def valid_file(arg):
    if os.path.isfile(arg):
        return arg
    raise argparse.ArgumentTypeError(f"{arg} is not an existing file!")


DESCRIPTION = (
    "STEA is a powerful economic analysis tool used for complex economic "
    "analysis and portfolio optimization. STEA helps you analyze single "
    "projects, large and small portfolios and complex decision trees. "
    "As output, for each of the entries in the result section of the "
    "yaml config file, STEA will create result files "
    "ex: Res1_0, Res2_0, .. Res#_0"
)


def _get_args_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument(
        "-c",
        "--config",
        help="STEA config file, yaml format required",
        type=valid_file,
    )
    parser.add_argument(
        "-r",
        "--response_file",
        help="STEA response, json format",
        default="stea_response.json",
    )
    parser.add_argument(
        "-e",
        "--ecl_case",
        help="Case name, will overwrite the value in the config if provided",
        default=None,
    )
    return parser


def main_entry_point():
    parser = _get_args_parser()
    options = parser.parse_args()
    if options.ecl_case == "__NONE__":  # This is because ert cant handle optionals
        options.ecl_case = None
    stea_input = stea.SteaInput([options.config, "--ecl_case", options.ecl_case])
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
    with open(options.response_file, "w", encoding="utf-8") as fout:
        json.dump(full_response, fout, indent=4)


def _get_profiles(server, project_id, project_version, config_date):
    client = stea.SteaClient(server)
    project = client.get_project(project_id, project_version, config_date)
    return project.profiles


def _build_full_response(result, profiles):
    return {"response": result, "profiles": profiles}


@hook_implementation
@plugin_response(plugin_name="fmu-steaclient")
def installable_jobs():
    return {"STEA": resource_filename("stea", "fm_stea/STEA_CONFIG")}


@hook_implementation
@plugin_response(plugin_name="fmu-steaclient")
def job_documentation(job_name):
    if job_name != "STEA":
        return None

    description = DESCRIPTION
    examples = ""
    category = "modelling.financial"

    return {
        "description": description,
        "examples": examples,
        "category": category,
    }
