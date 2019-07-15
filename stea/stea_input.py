from argparse import ArgumentParser
import os.path
import datetime
import yaml
import configsuite
from .stea_config import _build_schema



try:
    from ecl.summary import EclSum
except ImportError:
    from ert.ecl import EclSum


def parse_date(date_input):
    if isinstance(date_input,datetime.date):
        return datetime.datetime(date_input.year, date_input.month, date_input.day)

    if isinstance(date_input, datetime.datetime):
        return date_input

    return datetime.datetime.strptime(date_input, "%Y-%m-%d")

def parse_args(argv):
    parser = ArgumentParser()
    parser.add_argument("config_file")
    parser.add_argument("--{}".format('ecl_case'), dest="ecl_case")
    return parser.parse_args(argv)


class SteaInput(object):

    def __init__(self, argv):
        args = parse_args(argv)
        if not os.path.isfile(args.config_file):
            raise IOError("No such file:{}".format(args.config_file))

        try:
            schema = _build_schema()
            defaults = {'stea_server': "https://ws2291.statoil.net", 'profiles': {}}
            with open(args.config_file, "r") as config_file:
                config = configsuite.ConfigSuite(
                    yaml.safe_load(config_file),
                    schema,
                    layers=(defaults,))

            if not config.valid:
                raise ValueError('Config file is not a valid config file: {}'.format(config.errors))

            self.config = config

        except Exception as ex:
            raise ValueError("Could not load config file: {file}\nFull message: {ex}".format(
                file=args.config_file,
                ex=ex)
            )

        if args.ecl_case:
            ecl_case_data = {'ecl_case':args.ecl_case}
            self.config = self.config.push(ecl_case_data)

        if self.ecl_case is not None:
            self.ecl_case = EclSum(self.ecl_case)

    def __getattr__(self, key):
        return self.config.snapshot.__getattribute__(key)


