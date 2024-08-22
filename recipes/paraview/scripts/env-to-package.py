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
parser.add_argument("-p", "--packagename", default="temppackage", help="Name of the package")
parser.add_argument("-a", "--add", action="store_true", help="Add the new package directly to the existing spack installation")
args = parser.parse_args()

# create a new directory called 'package'
if not os.path.exists("packages"):
    os.makedirs("packages")
# remove any hyphens from the package name and capitalize the first letter of each word
packagenameU = args.packagename.replace("-", " ").title().replace(" ", "")
print(f"Package name: {packagenameU}")

# read the yaml file
with open(f'{args.filename}', 'r') as stream:
    try:
        env = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

# change the following generation of the file to a string with the same contents
output = f"# This file was auto-generated from {args.filename}\n"
output += "\n"
output += "import itertools, os, sys\n"
output += "from spack import *\n"
output += "\n"
output +=f"class {packagenameU}(CMakePackage):\n"
output += "    homepage = \"https://www.dummy.org/\"\n"
output += "    url      = \"https://www.dummy.org/\"\n"
output += "    git      = \"https://www.dummy.org/\"\n"
output += "\n"
output += "    version(\"develop\", branch=\"main\")\n"

# extract the dependencies from the yaml specs section, assume 'spec' is one level down from top level key 
# doign this allows us to import an env from stackinator, or a regular env yaml file
try:
    specs = env[list(env.keys())[0]]['specs']
except KeyError:
    print("No specs found in the yaml file - is 'spec' a top level key?")
    sys.exit(1)

dependencies = []
for spec in specs:
    output += f"    depends_on(\"{spec}\")\n"
    # 
print(output)

if args.add:
    spack_package_root = os.popen('spack location -r').read().strip() + "/var/spack/repos/builtin/packages"
    tempdir = os.path.join(spack_package_root, args.packagename)
else:
    # create a subdir named after the package if the subdir doesn't already exist
    tempdir = os.path.join("./packages", args.packagename)

if not os.path.exists(tempdir):
    os.makedirs(tempdir)
print('Writing temp package to ' + os.path.join(tempdir, 'package.py'))

# create a temp file in the directory
tempfile = os.path.join(tempdir, 'package.py')
with open(tempfile, 'w') as f:
    f.write(output)
    f.close()
    print(f"Temporary file {tempfile} has been created")

print(f'spackgen {args.packagename} "{args.packagename} %gcc" --reuse')

with open('./repo.yaml', 'w') as f:
    f.write(f"repo:\n")
    f.write(f"  namespace: 'userenv'\n")
    f.close()
    print("Repo file has been created")

