#!/usr/bin/env python

from setuptools import setup

setup(
    name="fmu-steaclient",
    description="stea - calculate economic analysis",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Scout, Equinor ASA",
    url="https://github.com/equinor/fmu-steaclient",
    packages=["stea"],
    setup_requires=["setuptools_scm"],
    use_scm_version={"write_to": "stea/version.py"},
    platforms="any",
    install_requires=["requests", "pyyaml", "configsuite>=0.6", "resdata"],
    test_suite="tests.suite",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        (
            "License :: OSI Approved :: "
            "GNU Lesser General Public License v3 or later (LGPLv3+)"
        ),
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
