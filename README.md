# Alps Uenv Recipes

This repository manages the recipes for uenv on CSCS' Alps clusters, and the definition of the CI/CD pipeline that deploys them.

See the [documentation](https://eth-cscs.github.io/alps-uenv/) for an overview of the uenv, and a packaging guide.

### First steps

The project is structured as follows: 

    .
    ├── ci                      # CI/CD pipeline configuration file
    ├── docs                    # Documentation files, see `mkdocs.yml`
    ├── recipes                 # uenv configuration files based on spack
    ├── workflow                # pipeline scripts and utils
    ├── README.md
    ├── config.yaml             # define available target systems for uenv build
    └── mkdocs.yml 

Creating a new uenv can be accomplished by adding a new recipe to the `recipes` folder as laid out under [recipe writing best practices](https://eth-cscs.github.io/alps-uenv/pkg-application-tutorial/) and updating the top-level `config.yaml` file with the uenv information and matching target system. The uenv itself is created via the script found in the `workflow` folder:

    .
    ├── workflow                    # scripts and utils
    │   ├── pipeline                # CI/CD utils
    │   ├── util                    # auxiliary scripts for uenv build and test
    │   ├── configure-pipeline      
    │   ├── stage-build             # script executed during pipeline build stage
    │   └── stage-test              # script executed during pipeline test stage
    └── ...

If testing locally, first invoke `configure-pipeline` to the `pipeline.yml` configuration file for the given target system. This file will then be consumed during the execution of the `stage-build` and `stage-test` scripts, which can be triggered locally for testing purposes but will in general be executed directly by the CI/CD runner. 