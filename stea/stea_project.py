from .stea_keys import SteaKeys


class SteaProject:
    def __init__(self, data):
        self.profiles = {
            profile[SteaKeys.PROFILE_ID]: profile for profile in data[SteaKeys.PROFILES]
        }
        self.project_id = data[SteaKeys.PROJECT_ID]
        self.project_version = data[SteaKeys.PROJECT_VERSION]

    def has_profile(self, profile_id):
        return profile_id in self.profiles

    def get_profile(self, profile_id):
        return self.profiles[profile_id]

    def get_profile_unit(self, profile_id):
        profile = self.get_profile(profile_id)
        return profile[SteaKeys.UNIT]

    def get_profile_mult(self, profile_id):
        profile = self.get_profile(profile_id)
        return profile.get(SteaKeys.MULTIPLE, "1")
