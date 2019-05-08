import configsuite
from configsuite import MetaKeys as MK
from configsuite import types

@configsuite.transformation_msg("Fix key names by replacing: `-` with `_`")
def _fix_keys(elem):
    fix_dict = {}
    for key in elem:
        new_key = str(key).replace('-','_')
        print('Replacing {} with {}'.format(key, new_key))
        fix_dict[new_key] = elem.get(key)
    return fix_dict

def _build_schema():
    return {
        MK.Type: types.NamedDict,
        MK.LayerTransformation: _fix_keys,
        MK.Content: {
            'project_id': {
                MK.Type: types.Number,
                MK.Description: ("The id (a number) of the project, which must already exist and be available in"
                                 "the stea database. In the Stea documentation this is called 'AlternativeId'"),
                MK.Required: True
            },
            'project_version': {
                MK.Type: types.Number,
                MK.Description: "Project alternative version number that comes from stea database",
                MK.Required: True
            },
            'config_date': {
                MK.Type: types.DateTime,
                MK.Description: "timestamp: Y-M-D H:M:S that comes with stea request",
                MK.Required: True
            },
            'profiles': {
                MK.Type: types.Dict,
                MK.Description: ("The profiles keyword is used to enter profile data explicitly in the"
                                "configuration file. Each profile is identified with an id from the"
                                "existing stea project, a start year and the actual data"),
                MK.Required: False,
                MK.Content: {
                    MK.Key: {MK.Type: types.String},
                    MK.Value: {
                        MK.Type: types.NamedDict,
                        MK.LayerTransformation: _fix_keys,
                        MK.Required: False,
                        MK.Content: {
                            'start_year': {
                                MK.Type: types.Integer,
                                MK.Description: "Start year (an Integer)",
                                MK.Required: False
                            },
                            'data': {
                                MK.Type: types.List,
                                MK.Description: "Values",
                                MK.Required: False,
                                MK.Content: {
                                    MK.Item: {MK.Type: types.Number}
                                }
                            }
                        }
                    }
                }
            },
            'ecl_profiles': {
                MK.Type: types.Dict,
                MK.Description: ("Profiles which are calculated directly from an eclipse simulation."
                                 "They are listed with the ecl-profiles ecl_key."),
                MK.Required: True,
                MK.Content: {
                    MK.Key: {MK.Type: types.String},
                    MK.Value: {
                        MK.Type: types.NamedDict,
                        MK.LayerTransformation: _fix_keys,
                        MK.Required: True,
                        MK.Content: {
                            'ecl_key': {
                                MK.Type: types.String,
                                MK.Description: "Summary key",
                                MK.Required: True
                            },
                            'start_year': {
                                MK.Type: types.Integer,
                                MK.Description: ("By default the stea"
                                                "client will calculate a profile from the full time range of the simulated"
                                                "data, but you can optionally use the keywords start-year and end-year to"
                                                "limit the time range."),
                                MK.Required: False
                            },
                            'end_year': {
                                MK.Type: types.Integer,
                                MK.Description: ("By default the stea"
                                                "client will calculate a profile from the full time range of the simulated"
                                                "data, but you can optionally use the keywords start-year and end-year to"
                                                "limit the time range."),
                                MK.Required: False
                            },
                            'mult': {
                                MK.Type: types.List,
                                MK.Required: False,
                                MK.Description: "List of multipliers of eclsum key",
                                MK.Content: {
                                    MK.Item: {
                                        MK.Type: types.Number
                                    }
                                }
                            },
                            'glob_mult': {
                                MK.Type: types.Number,
                                MK.Required: False,
                                MK.Description: "A single global multiplier of eclsum key",
                                MK.Content: {
                                    MK.Item: {
                                        MK.Type: types.Integer
                                    }
                                }
                            },
                        }
                    }
                }
            },
            'stea_server': {
               MK.Type: types.String,
               MK.Description: "stea server host.",
               MK.Required: False
            },
            'ecl_case': {
                MK.Type: types.String,
                MK.Description: "ecl case location",
                MK.Required: False
            },
            'results': {
                MK.Type: types.List,
                MK.Description: ("Specify what STEA should calculate"),
                MK.Required: True,
                MK.Content: {
                    MK.Item: {
                        MK.Type: types.String
                    }
                }
            },
        },
    }
