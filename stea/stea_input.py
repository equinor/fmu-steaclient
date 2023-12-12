import os.path
from argparse import ArgumentParser

import yaml
from resdata.summary import Summary

from .stea_config import SteaConfig


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
            with open(args.config_file, "r", encoding="utf-8") as config_file:
                config_dict = yaml.safe_load(config_file)

                if args.ecl_case:
                    config_dict["ecl_case"] = args.ecl_case

                config = SteaConfig(**config_dict)

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
        return self.config.__getattribute__(key)
