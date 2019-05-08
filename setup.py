#!/usr/bin/env python

from setuptools import setup, Extension

long_description = """
=======
stea
=======

Introduction
------------

"""

setup(name='stea',
      description='stea - calculate economic analysis',
      long_description=long_description,
      author='Statoil ASA',
      author_email='joaho@statoil.com',
      url='https://github.com/Statoil/stea',
      packages=['stea'],
      setup_requires=['setuptools_scm'],
      use_scm_version={'write_to' : 'stea/version.py'},
      platforms='any',
      install_requires=['requests','pyyaml','configsuite'],
      test_suite='tests.suite',
)
