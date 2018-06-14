from argparse import ArgumentParser
import os.path
import datetime
import yaml
import argparse
from .stea_client import SteaClient
from .stea_keys import SteaInputKeys, SteaKeys

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

stea_server = "https://st-WS2291.statoil.net"


def parse_args(argv):
    parser = ArgumentParser()
    parser.add_argument("config_file")
    parser.add_argument("--{}".format(SteaInputKeys.ECL_CASE), dest="ecl_case")
    return parser.parse_args(argv)


class SteaInput(object):

    def __init__(self, argv):
        args = parse_args( argv )
        if not os.path.isfile(args.config_file):
            raise IOError("No such file:{}".format(args.config_file))

        try:
            config = yaml.load(open(args.config_file))
        except:
            raise ValueError("Could not load config file: {}".format(args.config_file))

        if args.ecl_case:
            config[SteaInputKeys.ECL_CASE] = args.ecl_case


        self.config_date = parse_date(config[SteaInputKeys.CONFIG_DATE])
        self.project_id = config[SteaInputKeys.PROJECT_ID]
        self.project_version = config[SteaInputKeys.PROJECT_VERSION]
        self.results = config[SteaInputKeys.RESULTS]
        self.server = config.get(SteaInputKeys.SERVER, stea_server_prod)

        self.profiles = {}
        for profile_id,profile_data in config.get(SteaInputKeys.PROFILES, {}).items():
            self.profiles[profile_id] = profile_data

        self.ecl_profiles = {}
        for profile_id, profile_data in config.get(SteaInputKeys.ECL_PROFILES, {}).items():
            self.ecl_profiles[profile_id] = profile_data

        self.ecl_case = None
        if SteaInputKeys.ECL_CASE in config:
            self.ecl_case = EclSum(config[SteaInputKeys.ECL_CASE])


