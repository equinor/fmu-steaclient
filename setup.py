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
      author_email='fg_gpl@statoil.com',
      url='https://github.com/Statoil/stea',
      packages=['stea'],
      setup_requires=['setuptools'],
      license='GPL-3.0',
      platforms='any',
      install_requires=['requests'],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Other Environment',
          'Intended Audience :: Developers',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Natural Language :: English',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Topic :: Software Development :: Libraries',
          'Topic :: Utilities'
      ],
      test_suite='tests',
)
