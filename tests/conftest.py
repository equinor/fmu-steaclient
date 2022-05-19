import pytest

from stea import SteaKeys, SteaProject


@pytest.fixture
def mock_project():
    return SteaProject(
        {
            SteaKeys.PROFILES: [
                {
                    SteaKeys.PROFILE_ID: "ID1",
                    SteaKeys.UNIT: "unit1",
                    SteaKeys.MULTIPLE: "Mill",
                },
                {SteaKeys.PROFILE_ID: "ID2", SteaKeys.UNIT: "unit2"},
            ],
            SteaKeys.PROJECT_ID: "project-id",
            SteaKeys.PROJECT_VERSION: "100",
        }
    )


@pytest.fixture
def mock_result():
    return {
        SteaKeys.KEY_VALUES: [
            {SteaKeys.TAX_MODE: SteaKeys.PRETAX, SteaKeys.VALUES: {"NPV": 123}},
            {SteaKeys.TAX_MODE: SteaKeys.CORPORATE, SteaKeys.VALUES: {"NPV": 456}},
        ]
    }
