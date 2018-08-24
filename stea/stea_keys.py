class SteaKeys(object):
    """The SteaKeys class contains string constants which are used in HTTP
    communication with the stea web service.
    """
    PROJECT_VERSION = "AlternativeVersion"
    PROJECT_ID      = "AlternativeId"
    PROFILES        = "Profiles"
    PROFILE_ID      = "Id"
    UNIT            = "Unit"
    MULTIPLE        = "Multiple"
    CONFIG_DATE     = "ConfigurationDate"
    RESULTS         = "Results"
    ADJUSTMENTS     = "Adjustments"
    START_YEAR      = "StartYear"
    DATA_INNER      = "Data"
    DATA_OUTER      = "Data"
    KEY_VALUES      = "KeyValues"
    VALUES          = "Values"
    TAX_MODE        = "TaxMode"

#   The PRETAX and CORPORATE values are actually not keys, but rather values
#   used with the TAX_MODE key.
    PRETAX          = "Pretax"
    CORPORATE       = "Corporate"


class SteaInputKeys(object):
    """The SteaInputKeys contains string constants used as keys in the
    configuration file used by the local stea client.
    """
    CONFIG_DATE     = "config-date"
    PROJECT_ID      = "project-id"
    PROJECT_VERSION = "project-version"
    RESULTS         = "results"
    ECL_PROFILES    = "ecl-profiles"
    ECL_CASE        = "ecl-case"
    ECL_KEY         = "ecl-key"
    ECL_MULT        = "mult"		
    SERVER          = "stea-server"
    START_YEAR      = "start-year"
    END_YEAR        = "end-year"
    PROFILES        = "profiles"
    DATA            = "data"
    PROFILE_KEY     = "Description"
