# read a yaml file and convert it to a spack package
# usage: python env-to-package.py <env.yaml> <package-name>
# example: python env-to-package.py paraview-env.yaml paraview

# load a yaml file
import yaml
import sys
import os

packagename = "temppackage"
packagenameU = packagename[0].upper() + packagename[1:]

# read the yaml file
filename = sys.argv[1]
with open(filename, 'r') as stream:
    try:
        env = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

# change the following generation of the file to a string with the same contents
output = f"# This file was auto-generated from {filename}\n"
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

# get SPACK_ROOT by executing shell command
spack_package_root = os.popen('spack location -r').read().strip() + "/var/spack/repos/builtin/packages"

# create a subdir named after the package if the subdir doesn't already exist
tempdir = os.path.join(spack_package_root, packagename)
if not os.path.exists(tempdir):
    os.makedirs(tempdir)
print('Writing temp package to ' + os.path.join(tempdir, 'package.py'))

# create a temp file in the directory
tempfile = os.path.join(tempdir, 'package.py')
with open(tempfile, 'w') as f:
    f.write(output)
    f.close()
    print(f"Temporary file {tempfile} has been created")

print(f'spackgen {packagename} "{packagename} %gcc" --reuse')


# call spack to install the package - print error if it fails

#os.system(f"spack info  {packagename}")
#os.system(f'. /home/biddisco/opt/spack.git/share/spack/setup-env.sh ; /home/biddisco/src/_env/devenv/spackgen.sh temp "{packagename}%gcc" --reuse')

# rewrite /home/biddisco/src/_env/bash/devenv/spackgen.sh as a python script

