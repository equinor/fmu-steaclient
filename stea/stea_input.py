from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from resdata.summary import Summary

from .stea_config import SteaConfig

if TYPE_CHECKING:
    from typing import Optional


class SteaInput:
    # pylint: disable=too-few-public-methods
    def __init__(self, config_file: Path, ecl_case: Optional[str] = None):
        try:
            with open(config_file, "r", encoding="utf-8") as fin:
                config_dict = yaml.safe_load(fin)
                if ecl_case:
                    if "ecl-case" in config_dict:
                        del config_dict["ecl-case"]
                    config_dict["ecl_case"] = ecl_case
                config = SteaConfig(**config_dict)

            self.config = config

        except Exception as ex:
            raise ValueError(
                f"Could not load config file: {config_file}, error: {ex}"
            ) from ex

        # pylint: disable=access-member-before-definition
        # (due to modified __getattr__)
        if self.ecl_case is not None:
            self.ecl_case = Summary(self.ecl_case)

    def __getattr__(self, key):
        """Make all values in the config available as object attributes"""
        return self.config.__getattribute__(key)
