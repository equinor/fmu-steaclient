import datetime

import configsuite
from configsuite import MetaKeys as MK
from configsuite import types


@configsuite.validator_msg("Must be defined")
def _is_not_empty(container):
    return len(container) > 0


@configsuite.transformation_msg("Fix key names by replacing: `-` with `_`")
def _fix_keys(elem):
    fix_dict = {}
    for key in elem:
        new_key = str(key).replace("-", "_")
        if key != new_key:
            print(f"Warning: Replacing deprecated {key} with {new_key}")
        fix_dict[new_key] = elem.get(key)
    return fix_dict


@configsuite.transformation_msg("fix dashes and transform deprecated start_year")
def _fix_keys_and_check_start_year(elem):
    no_dashes = _fix_keys(elem)
    if no_dashes.get("start_year") is not None:
        if no_dashes.get("start_date") is not None:
            # configsuite transforms before validation, so this validation
            # must be here.
            raise ValueError("Do not provide both start_year and start_date")
        print("Warning: start_year is deprecated, use start_date.")
        no_dashes["start_date"] = datetime.date(no_dashes.get("start_year"), 1, 1)
        del no_dashes["start_year"]
    return no_dashes


def _build_schema():
    return {
        MK.Type: types.NamedDict,
        MK.LayerTransformation: _fix_keys,
        MK.Content: {
            "project_id": {
                MK.Type: types.Number,
                MK.Description: (
                    "The id (a number) of the project, which must already "
                    "exist and be available in the stea database. In the "
                    "Stea documentation this is called 'AlternativeId'"
                ),
            },
            "project_version": {
                MK.Type: types.Number,
                MK.Description: (
                    "Project alternative version number that "
                    "comes from stea database"
                ),
            },
            "config_date": {
                MK.Type: types.DateTime,
                MK.Description: "timestamp: Y-M-D H:M:S that comes with stea request",
            },
            "profiles": {
                MK.Type: types.Dict,
                MK.Description: (
                    "The profiles keyword is used to enter profile data explicitly "
                    "in the configuration file. Each profile is identified with "
                    "an id from the existing stea project, a start year and the "
                    "actual data."
                ),
                MK.Content: {
                    MK.Key: {MK.Type: types.String},
                    MK.Value: {
                        MK.Type: types.NamedDict,
                        MK.LayerTransformation: _fix_keys,
                        MK.Content: {
                            "start_year": {
                                MK.Type: types.Integer,
                                MK.Description: "Start year (an Integer)",
                                MK.AllowNone: True,
                            },
                            "data": {
                                MK.Type: types.List,
                                MK.Description: "Values",
                                MK.Content: {
                                    MK.Item: {MK.Type: types.Number, MK.AllowNone: True}
                                },
                            },
                        },
                    },
                },
            },
            "ecl_profiles": {
                MK.Type: types.Dict,
                MK.ElementValidators: (_is_not_empty,),
                MK.Description: (
                    "Profiles which are calculated directly from an eclipse "
                    "simulation. They are listed with the ecl-profiles ecl_key."
                ),
                MK.Content: {
                    MK.Key: {MK.Type: types.String},
                    MK.Value: {
                        MK.Type: types.NamedDict,
                        MK.LayerTransformation: _fix_keys_and_check_start_year,
                        MK.Content: {
                            "ecl_key": {
                                MK.Type: types.String,
                                MK.Description: "Summary key",
                            },
                            "start_date": {
                                MK.Type: types.Date,
                                MK.Description: (
                                    "By default fmu-steaclient "
                                    "will calculate a profile from the full "
                                    "time range of the simulated data, but you can "
                                    "optionally use the keywords start_date and "
                                    "end_year to limit the time range. Production "
                                    "on the start_date is included. "
                                    "Date format is YYYY-MM-DD."
                                ),
                                MK.AllowNone: True,
                            },
                            "start_year": {
                                MK.Type: types.Integer,
                                MK.Description: "Deprecated. Use start_date",
                                MK.AllowNone: True,
                            },
                            "end_year": {
                                MK.Type: types.Integer,
                                MK.Description: (
                                    "Set an explicit last year for the data "
                                    "to extract from a profile. All data up until "
                                    "the last day of this year will be included."
                                ),
                                MK.AllowNone: True,
                            },
                            "mult": {
                                MK.Type: types.List,
                                MK.Description: "List of multipliers of summary key",
                                MK.Content: {
                                    MK.Item: {MK.Type: types.Number, MK.AllowNone: True}
                                },
                            },
                            "glob_mult": {
                                MK.Type: types.Number,
                                MK.Description: (
                                    "A single global multiplier of summary key"
                                ),
                                MK.AllowNone: True,
                            },
                        },
                    },
                },
            },
            "stea_server": {
                MK.Type: types.String,
                MK.Description: "stea server host.",
                MK.AllowNone: True,
            },
            "ecl_case": {
                MK.Type: types.String,
                MK.Description: "ecl case location",
                MK.AllowNone: True,
            },
            "results": {
                MK.Type: types.List,
                MK.ElementValidators: (_is_not_empty,),
                MK.Description: ("Specify what STEA should calculate"),
                MK.Content: {MK.Item: {MK.Type: types.String}},
            },
        },
    }
