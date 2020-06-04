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
        print("Replacing {} with {}".format(key, new_key))
        fix_dict[new_key] = elem.get(key)
    return fix_dict


def _build_schema():
    return {
        MK.Type: types.NamedDict,
        MK.LayerTransformation: _fix_keys,
        MK.Content: {
            "project_id": {
                MK.Type: types.Number,
                MK.Description: (
                    "The id (a number) of the project, which must already exist and be available in"
                    "the stea database. In the Stea documentation this is called 'AlternativeId'"
                ),
            },
            "project_version": {
                MK.Type: types.Number,
                MK.Description: "Project alternative version number that comes from stea database",
            },
            "config_date": {
                MK.Type: types.DateTime,
                MK.Description: "timestamp: Y-M-D H:M:S that comes with stea request",
            },
            "profiles": {
                MK.Type: types.Dict,
                MK.Description: (
                    "The profiles keyword is used to enter profile data explicitly in the"
                    "configuration file. Each profile is identified with an id from the"
                    "existing stea project, a start year and the actual data"
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
                    "Profiles which are calculated directly from an eclipse simulation."
                    "They are listed with the ecl-profiles ecl_key."
                ),
                MK.Content: {
                    MK.Key: {MK.Type: types.String},
                    MK.Value: {
                        MK.Type: types.NamedDict,
                        MK.LayerTransformation: _fix_keys,
                        MK.Content: {
                            "ecl_key": {
                                MK.Type: types.String,
                                MK.Description: "Summary key",
                            },
                            "start_year": {
                                MK.Type: types.Integer,
                                MK.Description: (
                                    "By default the stea"
                                    "client will calculate a profile from the full time range of the simulated"
                                    "data, but you can optionally use the keywords start-year and end-year to"
                                    "limit the time range."
                                ),
                                MK.AllowNone: True,
                            },
                            "end_year": {
                                MK.Type: types.Integer,
                                MK.Description: (
                                    "By default the stea"
                                    "client will calculate a profile from the full time range of the simulated"
                                    "data, but you can optionally use the keywords start-year and end-year to"
                                    "limit the time range."
                                ),
                                MK.AllowNone: True,
                            },
                            "mult": {
                                MK.Type: types.List,
                                MK.Description: "List of multipliers of eclsum key",
                                MK.Content: {
                                    MK.Item: {MK.Type: types.Number, MK.AllowNone: True}
                                },
                            },
                            "glob_mult": {
                                MK.Type: types.Number,
                                MK.Description: "A single global multiplier of eclsum key",
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
