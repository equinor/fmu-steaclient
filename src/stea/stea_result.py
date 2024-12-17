from .stea_keys import SteaKeys


class SteaResult:
    # pylint: disable=too-few-public-methods
    def __init__(self, data, stea_input):
        self.data = data
        self.stea_input = stea_input

    def results(self, tax_mode):
        res = {}
        for value_dict in self.data[SteaKeys.KEY_VALUES]:
            if value_dict[SteaKeys.TAX_MODE] == tax_mode:
                for res_key in self.stea_input.results:
                    res[res_key] = value_dict[SteaKeys.VALUES][res_key]

                return res

        raise KeyError(f"No such tax mode: {tax_mode}")
