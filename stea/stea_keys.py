# pylint: disable=too-few-public-methods


class SteaKeys:
    """The SteaKeys class contains string constants which are used in HTTP
    communication with the stea web service.
    """

    PRODUCTION_SERVER = "https://stea-fmu.equinor.com:1700"
    PROJECT_VERSION = "AlternativeVersion"
    PROJECT_ID = "AlternativeId"
    PROFILES = "Profiles"
    PROFILE_ID = "Id"
    UNIT = "Unit"
    MULTIPLE = "Multiple"
    CONFIG_DATE = "ConfigurationDate"
    RESULTS = "Results"
    ADJUSTMENTS = "Adjustments"
    START_YEAR = "StartYear"
    DATA_INNER = "Data"
    DATA_OUTER = "Data"
    KEY_VALUES = "KeyValues"
    VALUES = "Values"
    TAX_MODE = "TaxMode"

    #   The PRETAX and CORPORATE values are actually not keys, but rather values
    #   used with the TAX_MODE key.
    PRETAX = "Pretax"
    CORPORATE = "Corporate"


class SteaInputKeys:
    """The SteaInputKeys contains string constants used as keys in the
    configuration file used by the local stea client.
    """

    CONFIG_DATE = "config_date"
    PROJECT_ID = "project_id"
    PROJECT_VERSION = "project_version"
    RESULTS = "results"
    ECL_PROFILES = "ecl_profiles"
    ECL_CASE = "ecl_case"
    ECL_KEY = "ecl_key"
    ECL_MULT = "mult"
    ECL_GLOB_MULT = "glob_mult"
    SERVER = "stea_server"
    START_DATE = "start_date"
    START_YEAR = "start_year"  # Deprecated
    END_YEAR = "end_year"
    PROFILES = "profiles"
    DATA = "data"
    PROFILE_KEY = "Description"
