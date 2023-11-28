#!/usr/bin/env python3

import jsonschema
import pathlib
import sys
import yaml

prefix = pathlib.Path(__file__).parent.resolve()
root_path = prefix.parent.resolve()
recipe_path = root_path / "recipes"

sys.path = [prefix.as_posix()] + sys.path

import schema

### TODO ###
# read and validate the configuration

### TODO ###
# read environment variables that describe image(s) to build in this run
# - system
# - uarch
# - uenv:version

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
