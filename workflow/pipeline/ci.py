#!/usr/bin/env python3

import argparse
import jinja2
import jsonschema
import os
import pathlib
import sys
import yaml

prefix = pathlib.Path(__file__).parent.resolve()
root_path = prefix.parent.resolve().parent.resolve()

sys.path = [prefix.as_posix()] + sys.path

import configuration
import util

class EnvError(Exception):
    """EnvError when invalid environment variables are provided
    """

    def __init__(self, message):
        self.message = f"Environment: {message}"
        super().__init__(self.message)

def readenv(config, args):
    """
    returns a dictionary with the following fields:
    {
        'system': 'todi',
        'uarch': 'gh200',
        'uenv': 'gromacs',
        'version': '2023',
        'recipe': configuration.Version
    }

    based on the values of the environment variables:
        - system
        - uarch
        - uenv
    """

    system = args.system
    uarch = args.uarch
    target = args.uenv

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

    recipe = config.recipe(uenv, version, uarch)

    if recipe is None:
        raise EnvError(f"the recipe {uenv}/{version} is not available for the {uarch} target")

    return {
        "system": system,
        "uarch": uarch,
        "uenv": uenv,
        "version": version,
        "recipe": recipe,
    }

def make_argparser():
    parser = argparse.ArgumentParser(description=("Generate a build configuration for a spack stack from " "a recipe."))
    # strictly necessary always
    parser.add_argument("-s", "--system", required=True, type=str)
    parser.add_argument("-a", "--uarch", required=True, type=str)
    parser.add_argument("-o", "--output", required=True, type=str)
    # if config is split into clusters and recipes part, then
    # only the cluster part would be required always
    parser.add_argument("-c", "--config", required=True, type=str)
    # alternatively a user could provide a single recipe, instead of a uenv argument
    # that is looked up in the recipes path via the cluster config
    parser.add_argument("-r", "--recipes", required=True, type=str)
    parser.add_argument("-u", "--uenv", required=True, type=str)

    return parser

if __name__ == "__main__":
    ### TODO ###
    # read CLI arguments
    #   - output path for the pipeline.yml file (required)
    #   + path of the configuration file (required)
    #   - JOB_ID (if needed?)
    if os.getenv("UENVCITEST", default=None) is not None:
        os.environ["system"] = "santis"
        os.environ["uarch"] = "gh200"
        os.environ["uenv"] = "netcdf-tools:2024"

    try:
        parser = make_argparser()
        args = parser.parse_args()
    except Exception as e:
        print(f"ERROR parsing CLI arguments: str(e)")
        exit(1)

    # read and validate the configuration
    try:
        config = configuration.Config(pathlib.Path(args.config),pathlib.Path(args.recipes))

    except jsonschema.exceptions.ValidationError as e:
        print()
        where = e.json_path.replace("$.","").replace(".", ":")
        print(f"{util.colorize('[error] ', 'red')}config.yaml:{where}")
        print(f"  {e.message}")
        exit(1)
    except configuration.ConfigError as e:
        print()
        print(f"{util.colorize('[error] ', 'red')}{e.message}")
        exit(1)

    # read environment variables that describe image(s) to build in this run
    try:
        env = readenv(config, args)
    except EnvError as e:
        print()
        print(f"{util.colorize('[error] ', 'red')}{e.message}")
        exit(1)

    print(f"--- request -----------------------------------------")
    for k,i in env.items():
        print(f"{k:20s}: {i}")

    print(f"\n--- job template ------------------------------------")
    job = config.job_template(env)
    for k,i in job.items():
        print(f"{k:20s}: {i}")

    #
    # write the pipeline.yml using jinja template
    #

    # load the jinja templating environment
    template_path = prefix / "templates"
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # generate top level makefiles
    pipeline_template = jinja_env.get_template("pipeline.yml")

    output_path = pathlib.Path(args.output)
    with output_path.open("w") as f:
        f.write(pipeline_template.render(jobs=[job]))

    print(f"\n{util.colorize('SUCCESS', 'green')} wrote {output_path} output file\n")

