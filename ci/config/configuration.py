#)!/usr/bin/env python3

import jsonschema
import pathlib
import sys
import yaml
import util

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

class Version:
    def __init__(self, name, desc, recipe_path):
        self._name = name
        self._recipes = desc["recipes"]
        self._deploy = desc["deploy"]
        self._use_spack_develop = desc["develop"]
        self._recipe_path = recipe_path

        arch = self.uarch

    @property
    def name(self):
        return self._name

    @property
    def spack_develop(self):
        return self._use_spack_develop

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

    def version(self, version):
        for v in self.versions:
            if v.name == version:
                return v
        return None

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
        print(util.colorize("Validating uenv configurations", "blue"))
        for uenv in self._uenvs:
            for version in uenv.versions:
                for cluster, deployments in version.deployments.items():
                    for uarch in deployments:
                        cstr = f"{uenv.name+'/'+version.name:25s} deploy {cluster+':'+uarch:18s}"
                        # verify that each deployment (cluster, uarch) exists
                        valid, reason = self.is_valid_target(cluster, uarch)
                        if not valid:
                            print(f"{cstr} {util.colorize('FAIL', 'red')} {reason}")
                            valid = False
                        # verify that this version has a recipe for the target uarch
                        elif uarch not in version.uarch:
                            print(f"{cstr} {util.colorize('FAIL', 'red')} no recipe for {uarch}")
                            valid = False
                        else:
                            print(f"{cstr} {util.colorize('PASS', 'green')}")

                for uarch in version.uarch:
                    cstr = f"{uenv.name+'/'+version.name:25s} recipe {uarch:18s}"
                    path = version.recipe(uarch)
                    if not path.exists():
                        print(f"{cstr} {util.colorize('FAIL', 'red')} recipe path {path.as_posix()} does not exist")
                        valid = False
                    else:
                        print(f"{cstr} {util.colorize('PASS', 'green')}")
        print()

        # Verify clusters
        print(util.colorize("Validating cluster configurations", "blue"))
        for name, cluster in self._clusters.items():
            cstr = f"{name}"
            # check that there is one partition for every uarch
            if len(cluster["partition"]) != len(cluster["uarch"]):
                print(f"{cstr:25s} {util.colorize('FAIL', 'red')} there must be exactly one partition for each uarch")
                valid = False
            # check that the FirecREST runner hasn't been selected (not supported yet)
            elif cluster["runner"] == "f7s":
                print(f"{cstr:25s} {util.colorize('WARN', 'cyan')} the FirecREST 'f7s' runner is not supported yet")
            else:
                print(f"{cstr:25s} {util.colorize('PASS', 'green')}")
        print()

        if not valid:
            raise ConfigError("configuration error - see log")

    def is_valid_target(self, cluster, uarch):
        if cluster not in self._clusters.keys():
            return False, f"cluster {cluster} is not defined"
        if uarch not in self._clusters[cluster]["uarch"]:
            return False, f"cluster {cluster} does not support {uarch}"
        return True, ""

    def uenv(self, name):
        """
        return the uenv information for uenv with name.
        returns None if no uenv matches name
        """
        for u in self.uenvs:
            if u.name == name:
                return u
        return None

    def recipe(self, name, version, uarch):
        """
        return the recipe information for uenv name:version on target uarch.
        returns None if no recipe fits the description.
        """
        u = self.uenv(name)
        if u is not None:
            for v in u.versions:
                if v.name==version and uarch in v.uarch:
                    return v.recipe(uarch)

        return None

    @property
    def uenvs(self):
        return self._uenvs

    @property
    def clusters(self):
        return self._clusters

    def job_template(self, env):
        """
        returns a dict that contains the information required to configure
        a gitlab runner job to build a recipe.
        The input is a dictionary with the following fields (with example values):
            system: clariden
            uarch: a100
            uenv: gromacs
            version: 2023
            recipe: /home/bcumming/software/github/alps-spack-stacks/recipes/gromacs/2023/a100
        """
        c = self.clusters[env["system"]]
        part_idx = c["uarch"].index(env["uarch"])

        develop = ""
        if self.uenv(env["uenv"]).version(env["version"]).spack_develop:
            develop = "--develop"

        return {
            "uenv": env["uenv"],
            "version": env["version"],
            "uarch": env["uarch"],
            "recipe_path": env["recipe"],
            "spack_develop": develop,
            "system": env["system"],
            "partition": c["partition"][part_idx],
            "baremetal_runner": c["runner"]["baremetal-tag"],
            "slurm_runner": c["runner"]["slurm-tag"],
        }

# load the uenv and cluster configurations
if __name__ == '__main__':
    try:
        config = Config(prefix / "config.yaml", recipe_path)
    except jsonschema.exceptions.ValidationError as e:
        print()
        where = e.json_path.replace("$.","").replace(".", ":")
        print(f"util.colorize('config.yaml error ... ', 'red') {where}")
        print(f"  {e.message}")
        exit(1)
    except ConfigError as e:
        print()
        print(f"{util.colorize('error ... ', 'red')}{e.message}")
        exit(1)

