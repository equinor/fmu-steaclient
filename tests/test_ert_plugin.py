from ert.plugins.plugin_manager import ErtPluginManager

import stea.fm_stea.fm_stea


def test_that_stea_hook_is_installed_in_ertpluginmanager() -> None:
    plugin_manager = ErtPluginManager(
        plugins=[
            stea.fm_stea.fm_stea,
        ]
    )
    assert plugin_manager.forward_model_steps[0]().name == "STEA"


def test_that_steaplugin_has_docs():
    plugin_manager = ErtPluginManager(plugins=[stea.fm_stea.fm_stea])

    docs = plugin_manager.forward_model_steps[0]().documentation()
    assert docs is not None
    assert docs.description is not None
    assert docs.category is not None
