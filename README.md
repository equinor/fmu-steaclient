[![Actions Status](https://github.com/equinor/stea/workflows/CI/badge.svg)](https://github.com/equinor/stea/actions?query=workflow=CI)


# fmu-steaclient

fmu-steaclient is a HTTP client for Stea calculations. The source code in this
project is a Python package, to actually use it you will need to write your own
executable script.

Stea is an Equinor application to perform economic analysis. The application is
an interactive windows application. In addition to the desktop application
there is a server solution for storage of projects and calculations service.
The purpose of this Python package is to invoke a Stea economic analysis on the
server.

The main way to configure the stea client is through a yaml file, an example
configuration file is shown here:

```yaml
# The id of the project, which must already exist and be available in
# the stea database. In the Stea documentation this is called "AlternativeId".
project-id: 4782
project-version: 1


# All information in stea is versioned with a timestamp. When we request a
# calculation we must specify wich date we wish to use to fetch configuration
# information for assumptions like e.g. the oil price.
config-date: 2018-07-01 12:00:00


# The stea web client works by *adjusting* the profiles in an existing
# stea project which has already been defined. That implies that all
# profiles added in this configuration file should already be part of
# the project. To match the profiles specified here with the profiles in
# the project we must give a id for the profiles.

# The profiles keyword is used to enter profile data explicitly in the
# configuration file. Each profile is identified with an id from the
# existing stea project, a start date and the actual data.

profiles:
    23fc0639-453f-42ee-876c-1e7b94a4f2bb:
       start-date: 2018-01-01
       data: [100, 200, 300]

# Profiles which are calculated directly from a reservoir simulation are
# listed with the ecl-profiles key. Each profile is identified with an id
# from the stea project and an key like 'FOPT'. By default the stea
# client will calculate a profile from the full time range of the simulated
# data, but you can optionally use the keywords start-date and end-year to
# limit the time range. All data in the end-year is included.
ecl-profiles:
  bf063de9-453f-42ee-876c-1e7b94a4f2bb:
     ecl-key: FOPT

  91e7b94a4f2bb-453f-42ee-876c-bf063de:
     ecl-key: FGPT
     start-date: 2020-01-01
     end-year: 2030

  profile_comment_in_stea:
     ecl-key: FWPT
     glob_mult: 1.1

  another_profile_comment_in_stea:
     ecl-key: FWPT
     mult: [ 1.1, 2, 0 ]

# When you use the ecl-profiles keyword to update profiles fetched directly
# from a reservoir simulation you also need to set the ecl-case keyword to
# point to an existing simulator summary case on disk
ecl-case: <PATH_TO_ECL_CASE>

# What do you want stea to calculate
results:
   - NPV
```

An minimal example script using the `fmu-steaclient` package could be:

```python
#!/usr/bin/env python
import sys
import stea

def main(argv):
    if len(argv) == 2:
       fname = argv[1]
    else:
        raise AttributeError('Need yaml formatted configuration file as first commandline argument')

    stea_input = stea.SteaInput(fname)
    res = stea.calculate(stea_input)
    for res, value in res.results(stea.SteaKeys.CORPORATE).items():
        print("{res} : {value}".format(res=res, value=value))


if __name__ == "__main__":
   main(sys.argv)

```


# Development


## Installation

Clone the repository and install in a virtual Python environment.
```sh
pip install -e ".[test]"
```

## Run tests
To run the test suite:

```sh
pytest
```

## Lint code

All commits to the repository must pass these commands, formatting and linting the code:
```sh
ruff check --fix .
ruff format .
```


## Developer information

This client only gives access to a very limited amount of the Stea
capabilities. The workflow for using this client is as follows:

 1. A Stea project is defined using the Stea desktop application. This project
    must be 100% complete.

 2. The profiles - i.e. yearly cost and income for the project can be adjusted,
    the principle for this client is to post adjusted profiles to the server.

### Class overview

#### SteaKeys

This a set of string constants which are used in the schema for HTTP
communication with the Stea server.

#### SteaInput

This is a small configuration object internalizing the input to the Stea
calculations. The input typically includes:

* Id of the Stea project, this is given both as an ID and a version.

* If of the profiles which can should be adjusted, and the eclipse key
  used to fetch them or alternatively the values themselves.

The input is currrently given as a YAML formatted file.

#### SteaInputKeys

A set of string constants used in the YAML input file.

#### SteaClient

A small class with a method to POST results to the Stea server and a method to
GET project data from the server.

#### SteaProject

Some information from the real stea project is needed to create the calculation
request. This information is internalized in the SteaProject class. The project
is created by doing a http GET from the server.

####  SteaRequest

The payload passed in the HTTP POST request is assembled in a SteaRequest
object.

#### SteaResult

Small wrapping of the return value from the stea calculation.
"""

>>>>>>> 69bdaa9 (Move documentation from source code to README)
