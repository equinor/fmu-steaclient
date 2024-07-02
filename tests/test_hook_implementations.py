from ert.shared.plugins.plugin_manager import ErtPluginManager

import stea.fm_stea.fm_stea


def test_hook_implementations():
    plugin_manager = ErtPluginManager(
        plugins=[
            stea.fm_stea.fm_stea,
        ]
    )
    installable_jobs = plugin_manager.get_installable_jobs()

    expected_jobname = "STEA"
    expected_jobscript = "stea/fm_stea/STEA_CONFIG"

    assert expected_jobname in installable_jobs
    assert installable_jobs["STEA"].endswith(expected_jobscript)


def test_hook_implementations_job_docs():
    plugin_manager = ErtPluginManager(plugins=[stea.fm_stea.fm_stea])

    installable_jobs = plugin_manager.get_installable_jobs()

    docs = plugin_manager.get_documentation_for_jobs()

    assert set(docs.keys()) == set(installable_jobs.keys())

    for job_name in installable_jobs:
        assert docs[job_name]["description"] != ""
        assert docs[job_name]["category"] != "other"
