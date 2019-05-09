# Stea [![Build Status](https://travis-ci.org/Statoil/stea.svg?branch=master)](https://travis-ci.org/Statoil/stea)

Stea is a HTTP client for Stea calculations, some documentation can be found in
the [stea/__init__.py](stea/__init__.py) file. The source code in this project
is a Python package, to actually use it you will need to write your own
executable script.

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
       start-year: 2018
       data: [100, 200, 300]

# Profiles which are calculated directly from an eclipse simulation are
# listed with the ecl-profiles key. Each profile is identified with an id 
# from the stea project and an eclipe key like 'FOPT'. By default the stea
# client will calculate a profile from the full time range of the simulated
# data, but you can optionally use the keywords start-year and end-year to
# limit the time range.
ecl-profiles:
  bf063de9-453f-42ee-876c-1e7b94a4f2bb:
     ecl-key: FOPT
     
  91e7b94a4f2bb-453f-42ee-876c-bf063de:
     ecl-key: FGPT
     start-year: 2020
     end-year: 2030
     
  profile_comment_in_stea:
     ecl-key: FWPT
     glob_mult: 1.1

  another_profile_comment_in_stea:
     ecl-key: FWPT
     mult: [ 1.1, 2, 0 ]  
 
# When you use the ecl-profiles keyword to update profiles feteched directly 
# from an eclipse simulation you also need to set the ecl-case keyword to
# point to an existing eclipse summary case on disk
ecl-case: models/eclipse/ECL_CASE_016

# What do you want stea to calculate
results: 
   - NPV
``` 

An minimal example script using the `stea` package could be:

```python
#!/usr/bin/env python
import sys
import stea

def main(argv):
     if len(argv) == 2:
        fname = argv[1]
    else:
        raise AttributeError('Need yaml formatted configuration file as first commandline argument')
    
    stea_input = stea.SteaInput([fname])
    res = stea.calculate(stea_input)
    for res,value in res.results(stea.SteaKeys.CORPORATE).items():
        print("{res} : {value}".format(res=res, value=value)) 
         
         
if __name__ == "__main__":
   main(sys.argv)

```
