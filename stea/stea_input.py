import datetime
import os.path
from argparse import ArgumentParser

import configsuite
import yaml
from resdata.summary import Summary

from .stea_config import _build_schema
from .stea_keys import SteaKeys


def parse_date(date_input):
    if isinstance(date_input, datetime.date):
        return datetime.datetime(date_input.year, date_input.month, date_input.day)

    if isinstance(date_input, datetime.datetime):
        return date_input

    return datetime.datetime.strptime(date_input, "%Y-%m-%d")


def parse_args(argv):
    parser = ArgumentParser()
    parser.add_argument("config_file")
    parser.add_argument(
        "--ecl_case",
        # Do not set type=str here, it will break.
        help="If supplied, it will overwrite any ecl_case supplied in the config file",
    )
    return parser.parse_args(argv)


class SteaInput:
    # pylint: disable=too-few-public-methods
    def __init__(self, argv):
        args = parse_args(argv)

        if not os.path.isfile(args.config_file):
            raise IOError(f"No such file: {args.config_file}")

        try:
            schema = _build_schema()
            defaults = {"stea_server": SteaKeys.PRODUCTION_SERVER}
            with open(args.config_file, "r", encoding="utf-8") as config_file:
                config_dict = yaml.safe_load(config_file)

                if args.ecl_case:
                    config_dict["ecl_case"] = args.ecl_case

                config = configsuite.ConfigSuite(
                    config_dict,
                    schema,
                    layers=(defaults,),
                    deduce_required=True,
                )

            if not config.valid:
                raise ValueError(
                    f"Config file is not a valid config file: {config.errors}"
                )

            self.config = config

        except Exception as ex:
            raise ValueError(
                f"Could not load config file: {args.config_file}, error: {ex}"
            ) from ex

        # pylint: disable=access-member-before-definition
        # (due to modified __getattr__)
        if self.ecl_case is not None:
            self.ecl_case = Summary(self.ecl_case)

    def __getattr__(self, key):
        """Make all values in the config available as object attributes"""
        return self.config.snapshot.__getattribute__(key)
