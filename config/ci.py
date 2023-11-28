#!/usr/bin/env python3

import jsonschema
import os
import pathlib
import sys
import yaml

prefix = pathlib.Path(__file__).parent.resolve()
root_path = prefix.parent.resolve()
recipe_path = root_path / "recipes"

sys.path = [prefix.as_posix()] + sys.path

import configuration
import util

class EnvError(Exception):
    """EnvError when invalid environment variables are provided
    """

    def __init__(self, message):
        self.message = f"Environment: {message}"
        super().__init__(self.message)

def readenv(config):
    """
    returns a dictionary with the following fields:
    {
        'system': 'clariden',
        'uarch': 'a100',
        'uenv': 'gromacs',
        'version': '2023',
        'recipe': configuration.Version
    }

    based on the values of the environment variables:
        - system
        - uarch
        - uenv
    """

    system = os.getenv("system", default=None)
    uarch = os.getenv("uarch", default=None)
    target = os.getenv("uenv", default=None)

    if system is None:
        raise EnvError("'system' environment variable not set")
    if uarch is None:
        raise EnvError("'uarch' environment variable not set")
    if target is None:
        raise EnvError("'uenv' environment variable not set")

    # check that system+uarch are valid
    if uarch not in configuration.valid_uarch:
        raise EnvError(f"uarch={uarch} is not one of the available options {configuration.valid_uarch}")
    valid, msg = config.is_valid_target(system, uarch)
    if not valid:
        raise EnvError(f"{msg}")

    try:
        uenv, version = target.split(':')
    except:
        raise EnvError(f"invalid format of uenv={target}, expected 'name:version'")

    # TODO: check that the recipe-version also supports uarch
    recipe = config.recipe(uenv, version, uarch)
    if recipe is None:
        raise EnvError(f"the recipe 'name:version' is not available")

    return {
        "system": system,
        "uarch": uarch,
        "uenv": uenv,
        "version": version,
        "recipe": recipe,
    }

if __name__ == '__main__':
    os.environ["system"] = "clariden"
    os.environ["uarch"] = "a100"
    os.environ["uenv"] = "gromacs:2023"

    # read and validate the configuration
    try:
        config = configuration.Config(prefix / "config.yaml", recipe_path)
    except jsonschema.exceptions.ValidationError as e:
        print()
        where = e.json_path.replace("$.","").replace(".", ":")
        print(f"util.colorize('[error] ', 'red')  config.yaml:{where}")
        print(f"  {e.message}")
        exit(1)
    except ConfigError as e:
        print()
        print(f"{util.colorize('[error] ', 'red')}{e.message}")
        exit(1)

    # read environment variables that describe image(s) to build in this run
    try:
        env = readenv(config)
    except EnvError as e:
        print()
        print(f"{util.colorize('[error] ', 'red')}{e.message}")
        exit(1)

    print(env)

### TODO ###
# read CLI arguments
#   - output path for the pipeline.yml file (required)
#   - path of the configuration file (required)
#   - JOB_ID (if needed?)

### TODO ###
# build list of all builds (system-uarch-recipe)
# include meta-data like the path in which to build

### TODO ###
# generate the build runner config info for each build job
# iterate over all builds and make a consolidated list of all target system+uarch
# follow naming scheme {system}-build-{uarch}, e.g. clariden-build-a100

### TODO ###
# make a template jinja yaml file externally

### TODO ###
# feed the tempalte to generate .yaml

# for cluster in clusters:
#   {cluster.name}-build-{cluster.uarch}:
#   tags: [{cluster.runner}]
#
#   {cluster.name}-test-{cluster.uarch}:
#   tags: [{cluster.bare_metal_runner}]

# for uenv in uenvs:
#   ...
