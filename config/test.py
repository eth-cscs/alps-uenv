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

valid_uarch = ["zen2", "zen3", "a100", "mi200"]

class ConfigError(Exception):
    """ConfigError when an invalid configuration is entered.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

def colorize(string, color):
    colors = {
        "red":     "31",
        "green":   "32",
        "yellow":  "33",
        "blue":    "34",
        "magenta": "35",
        "cyan":    "36",
        "white":   "37",
    }
    return f"\033[1;{colors[color]}m{string}\033[0m"

class Version:
    def __init__(self, name, desc, recipe_path):
        self._name = name
        self._recipes = desc["recipes"]
        self._deploy = desc["deploy"]
        self._recipe_path = recipe_path

        arch = self.uarch

    @property
    def name(self):
        return self._name

    @property
    def uarch(self):
        # list of the uarch that this version can be deployed on
        return [n for n in self._recipes.keys()]

    def recipe(self, uarch):
        return self._recipe_path / self._recipes[uarch]

    @property
    def deployments(self):
        return self._deploy

class Uenv:
    def __init__(self, name, desc, recipe_path):
        self._name = name
        self._versions = [Version(v, desc[v], recipe_path / name)  for v in desc.keys()]

    @property
    def name(self):
        return self._name

    @property
    def versions(self):
        return self._versions

class Config:
    def __init__(self, config_path, recipe_path):
        with config_path.open() as fid:
            config = yaml.load(fid, Loader=yaml.Loader)
            schema.config_validator.validate(config)
            self._uenvs = [Uenv(k, config["uenvs"][k], recipe_path) for k in config["uenvs"].keys()]
            self._clusters = config["clusters"]

        self._cluster_names = [n for n in self._clusters.keys()]

        # Validate the inputs
        #
        # The values in self._clusters are handled by the schema
        #

        # Verify that each target is a valid cluster.
        valid = True
        print(colorize("Validating uenv configurations", "blue"))
        for uenv in self._uenvs:
            for version in uenv.versions:
                for cluster, deployments in version.deployments.items():
                    for uarch in deployments:
                        cstr = f"{uenv.name+'/'+version.name:25s} deploy {cluster+':'+uarch:18s}"
                        # verify that each deployment (cluster, uarch) exists
                        valid, reason = self.is_valid_target(cluster, uarch)
                        if not valid:
                            print(f"{cstr} {colorize('FAIL', 'red')} {reason}")
                            valid = False
                        # verify that this version has a recipe for the target uarch
                        elif uarch not in version.uarch:
                            print(f"{cstr} {colorize('FAIL', 'red')} no recipe for {uarch}")
                            valid = False
                        else:
                            print(f"{cstr} {colorize('PASS', 'green')}")

                for uarch in version.uarch:
                    cstr = f"{uenv.name+'/'+version.name:25s} recipe {uarch:18s}"
                    path = version.recipe(uarch)
                    if not path.exists():
                        print(f"{cstr} {colorize('FAIL', 'red')} recipe path {path.as_posix()} does not exist")
                        valid = False
                    else:
                        print(f"{cstr} {colorize('PASS', 'green')}")

        # Verify clusters
        print(colorize("Validating cluster configurations", "blue"))
        for name, cluster in self._clusters.items():
            cstr = f"{name}"
            # check that there is one partition for every uarch
            if len(cluster["partition"]) != len(cluster["uarch"]):
                print(f"{cstr:25s} {colorize('FAIL', 'red')} there must be exactly one partition for each uarch")
                valid = False
            # check that the FirecREST runner hasn't been selected (not supported yet)
            elif cluster["runner"] == "f7s":
                print(f"{cstr:25s} {colorize('WARN', 'cyan')} the FirecREST 'f7s' runner is not supported yet")
            else:
                print(f"{cstr:25s} {colorize('PASS', 'green')}")


        if not valid:
            raise ConfigError("configuration error - see log")

    def is_valid_target(self, cluster, uarch):
        if cluster not in self._clusters.keys():
            return False, f"cluster {cluster} is not defined"
        if uarch not in self._clusters[cluster]["uarch"]:
            return False, f"cluster {cluster} does not support {uarch}"
        return True, ""

    @property
    def uenvs(self):
        return self._uenvs

    @property
    def clusters(self):
        return self._clusters

# The user request
class Request:

    def __init__(self, config):
        self._cluster = os.getenv('cluster', None)
        uenv = os.getenv('uenv', None)
        self._uarch = os.getenv('uarch', None)

        # error check, using config.

        uenv_name, uenv_version = uenv.split
        self._uenv = None
        self._version = None

    @property
    def cluster(self):
        return self._cluster

    @property
    def uenv(self):
        return self._uenv, self._version

    @property
    def uarch(self):
        return self._uarch


# load the uenv and cluster configurations
if __name__ == '__main__':
    try:
        config = Config(prefix / "config.yaml", recipe_path)
    except jsonschema.exceptions.ValidationError as e:
        print()
        where = e.json_path.replace("$.","").replace(".", ":")
        print(f"config.yaml error: {where}")
        print(f"  {e.message}")
        exit(1)
    except ConfigError as e:
        print()
        print(f"{e.message}")
        exit(1)

