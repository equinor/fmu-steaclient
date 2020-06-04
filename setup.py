#!/usr/bin/env python

from setuptools import setup

setup(
    name="stea",
    description="stea - calculate economic analysis",
    author="Software Innovation Bergen, Equinor ASA",
    url="https://github.com/equinor/stea",
    packages=["stea"],
    setup_requires=["setuptools_scm"],
    use_scm_version={"write_to": "stea/version.py"},
    platforms="any",
    install_requires=["requests", "pyyaml", "configsuite>=0.6"],
    test_suite="tests.suite",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
