# read a yaml file and convert it to a spack package
# usage: python env-to-package.py <env.yaml> <package-name>
# example: python env-to-package.py paraview-env.yaml paraview

# load a yaml file
import yaml
import sys
import os
import argparse

# read command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--filename", help="Path to the yaml file")
parser.add_argument(
    "-p", "--packagename", default="temppackage", help="Name of the package"
)
parser.add_argument(
    "-a",
    "--add",
    action="store_true",
    help="Add the new package directly to the existing spack installation",
)
args = parser.parse_args()

os.makedirs("packages", exist_ok=True)
pkg_class = args.packagename.replace("-", " ").title().replace(" ", "")
pkg_filename = args.packagename.replace(" ", "").replace("-", "_").lower()
print(f"Package name: {pkg_class}")

# read the yaml file
with open(f"{args.filename}", "r") as stream:
    env = yaml.safe_load(stream)

# change the following generation of the file to a string with the same contents
output = f"# This file was auto-generated from {args.filename}\n"
output += "\n"
output += "import itertools, os, sys\n"
output += "from spack.package import *\n"
output += "from spack_repo.builtin.build_systems.cmake import CMakePackage\n"
output += "\n"
output += f"class {pkg_class}(CMakePackage):\n"
output += '    homepage = "https://www.dummy.org/"\n'
output += '    url      = "https://www.dummy.org/"\n'
output += '    git      = "https://www.dummy.org/"\n'
output += "\n"
output += '    version("develop", branch="main")\n'
output += '    depends_on("c", type="build")\n'
output += '    depends_on("cxx", type="build")\n'

# extract the dependencies from the yaml specs section, assume 'spec' is one level down from top level key
# doing this allows us to import an env from stackinator, or a regular env yaml file
try:
    specs = env[list(env.keys())[0]]["specs"]
except KeyError:
    print("No specs found in the yaml file - is 'spec' a top level key?")
    sys.exit(1)

dependencies = []
for spec in specs:
    output += f'    depends_on("{spec}")\n'
print(output)

if args.add:
    spack_package_root = os.popen("spack location --repo").read().strip() + "/packages"
    tempdir = os.path.join(spack_package_root, pkg_filename)
else:
    # create a subdir named after the package if the subdir doesn't already exist
    tempdir = os.path.join("./packages", pkg_filename)

os.makedirs(tempdir, exist_ok=True)
print("Writing temp package to " + os.path.join(tempdir, "package.py"))

# create a temp file in the directory
tempfile = os.path.join(tempdir, "package.py")
with open(tempfile, "w") as f:
    f.write(output)
    f.close()
    print(f"Temporary file {tempfile} has been created")
